from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Profile
from cargo.models import Cargo
from clients.models import Client
from drivers.models import Driver
from expenses.models import Expense
from maintenance.models import Maintenance
from notifications.models import Notification
from payments.models import Payment
from reports.views import get_date_range
from trips.models import Trip
from trucks.models import Truck

from .serializers import (
    CargoSerializer,
    ClientSerializer,
    DriverSerializer,
    ExpenseSerializer,
    MaintenanceSerializer,
    NotificationSerializer,
    PaymentSerializer,
    ProfileSerializer,
    TripSerializer,
    TruckSerializer,
    UserSerializer,
)


def _decimal_text(value):
    return f"{Decimal(value or 0):.2f}"


def _choices(choices):
    return [{"value": value, "label": label} for value, label in choices]


def _is_admin_role(user):
    return bool(user and user.is_authenticated and getattr(getattr(user, "profile", None), "role", None) == "admin")


class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return _is_admin_role(request.user)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().select_related("profile")
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]


class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer

    def get_queryset(self):
        queryset = Profile.objects.select_related("user")
        if _is_admin_role(self.request.user):
            return queryset
        return queryset.filter(user=self.request.user)


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class TruckViewSet(viewsets.ModelViewSet):
    queryset = Truck.objects.all()
    serializer_class = TruckSerializer


class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.select_related("user", "assigned_truck")
    serializer_class = DriverSerializer


class TripViewSet(viewsets.ModelViewSet):
    serializer_class = TripSerializer

    def get_queryset(self):
        queryset = Trip.objects.select_related("client", "assigned_truck", "assigned_driver", "created_by")
        status_filter = self.request.query_params.get("status")
        query = self.request.query_params.get("q")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if query:
            queryset = queryset.filter(
                Q(reference_number__icontains=query)
                | Q(client__client_name__icontains=query)
                | Q(pickup_location__icontains=query)
                | Q(dropoff_location__icontains=query)
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["patch"])
    def status(self, request, pk=None):
        trip = self.get_object()
        next_status = request.data.get("status")
        valid_statuses = dict(Trip.STATUS_CHOICES)
        if next_status not in valid_statuses:
            return Response(
                {"status": [f"Must be one of: {', '.join(valid_statuses.keys())}."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        trip.status = next_status
        if next_status == "in_transit" and not trip.actual_pickup:
            trip.actual_pickup = timezone.now()
        if next_status == "delivered" and not trip.actual_delivery:
            trip.actual_delivery = timezone.now()
        trip.save()
        return Response(self.get_serializer(trip).data)


class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.select_related("trip")
    serializer_class = CargoSerializer


class MaintenanceViewSet(viewsets.ModelViewSet):
    queryset = Maintenance.objects.select_related("truck")
    serializer_class = MaintenanceSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.select_related("trip", "truck")
    serializer_class = ExpenseSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("trip", "client")
    serializer_class = PaymentSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(self.get_serializer(notification).data)


class DashboardSummaryView(APIView):
    def get(self, request):
        today = timezone.now().date()
        monthly_revenue = Payment.objects.filter(
            payment_date__year=today.year,
            payment_date__month=today.month,
            payment_status="paid",
        ).aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
        monthly_expenses = Expense.objects.filter(
            date__year=today.year,
            date__month=today.month,
        ).aggregate(Sum("amount"))["amount__sum"] or 0
        return Response(
            {
                "total_trucks": Truck.objects.count(),
                "available_trucks": Truck.objects.filter(status="available").count(),
                "maintenance_trucks": Truck.objects.filter(status="maintenance").count(),
                "total_drivers": Driver.objects.count(),
                "active_drivers": Driver.objects.filter(employment_status="active").count(),
                "active_trips": Trip.objects.filter(status__in=["scheduled", "loading", "in_transit"]).count(),
                "pending_trips": Trip.objects.filter(status="pending").count(),
                "completed_trips": Trip.objects.filter(status="delivered").count(),
                "cancelled_trips": Trip.objects.filter(status="cancelled").count(),
                "monthly_revenue": _decimal_text(monthly_revenue),
                "monthly_expenses": _decimal_text(monthly_expenses),
                "overdue_maintenance": Maintenance.objects.filter(
                    next_service_date__lt=today,
                    status__in=["scheduled", "ongoing"],
                ).count(),
                "expiring_registrations": Truck.objects.filter(
                    registration_expiry__gte=today,
                    registration_expiry__lte=today + timezone.timedelta(days=30),
                ).count(),
                "unpaid_payments": Payment.objects.filter(payment_status="unpaid").count(),
            }
        )


class ChoiceMetadataView(APIView):
    def get(self, request):
        return Response(
            {
                "accounts": {"roles": _choices(Profile.ROLE_CHOICES)},
                "trucks": {
                    "types": _choices(Truck.TRUCK_TYPES),
                    "status": _choices(Truck.STATUS_CHOICES),
                },
                "drivers": {"employment_status": _choices(Driver.EMPLOYMENT_STATUS)},
                "trips": {"status": _choices(Trip.STATUS_CHOICES)},
                "cargo": {"condition": _choices(Cargo.CONDITION_CHOICES)},
                "maintenance": {
                    "types": _choices(Maintenance.MAINTENANCE_TYPES),
                    "status": _choices(Maintenance.STATUS_CHOICES),
                },
                "expenses": {"types": _choices(Expense.EXPENSE_TYPES)},
                "payments": {"status": _choices(Payment.STATUS_CHOICES)},
                "notifications": {"types": _choices(Notification.NOTIFICATION_TYPES)},
            }
        )


class DailyTripReportView(APIView):
    def get(self, request):
        start, end = get_date_range(request)
        trips = Trip.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
        status_filter = request.query_params.get("status", "")
        if status_filter:
            trips = trips.filter(status=status_filter)
        return Response(
            {
                "start": start,
                "end": end,
                "status": status_filter,
                "total_trips": trips.count(),
                "results": TripSerializer(trips, many=True, context={"request": request}).data,
            }
        )


class MonthlyTripReportView(APIView):
    def get(self, request):
        start, end = get_date_range(request)
        trips = Trip.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
        return Response(
            {
                "start": start,
                "end": end,
                "total_trips": trips.count(),
                "completed_trips": trips.filter(status="delivered").count(),
                "cancelled_trips": trips.filter(status="cancelled").count(),
                "in_transit_trips": trips.filter(status="in_transit").count(),
                "results": TripSerializer(trips, many=True, context={"request": request}).data,
            }
        )


class TruckUtilizationReportView(APIView):
    def get(self, request):
        trucks = Truck.objects.annotate(
            total_trips=Count("trips"),
            completed_trips=Count("trips", filter=Q(trips__status="delivered")),
        )
        return Response(
            {
                "results": [
                    {
                        "id": truck.id,
                        "plate_number": truck.plate_number,
                        "truck_type": truck.truck_type,
                        "truck_type_display": truck.get_truck_type_display(),
                        "status": truck.status,
                        "status_display": truck.get_status_display(),
                        "total_trips": truck.total_trips,
                        "completed_trips": truck.completed_trips,
                    }
                    for truck in trucks
                ]
            }
        )


class DriverPerformanceReportView(APIView):
    def get(self, request):
        drivers = Driver.objects.annotate(
            total_trips=Count("trips"),
            completed_trips=Count("trips", filter=Q(trips__status="delivered")),
        )
        results = []
        for driver in drivers:
            cancelled_trips = max(driver.total_trips - driver.completed_trips, 0)
            completion_rate = (
                round(driver.completed_trips / driver.total_trips * 100, 2)
                if driver.total_trips
                else 0
            )
            results.append(
                {
                    "id": driver.id,
                    "full_name": driver.full_name,
                    "total_trips": driver.total_trips,
                    "completed_trips": driver.completed_trips,
                    "cancelled_trips": cancelled_trips,
                    "completion_rate": completion_rate,
                }
            )
        return Response({"results": results})


class MaintenanceReportView(APIView):
    def get(self, request):
        start, end = get_date_range(request)
        records = Maintenance.objects.filter(service_date__gte=start, service_date__lte=end)
        total_cost = records.aggregate(Sum("cost"))["cost__sum"] or 0
        return Response(
            {
                "start": start,
                "end": end,
                "total_cost": _decimal_text(total_cost),
                "results": MaintenanceSerializer(records, many=True, context={"request": request}).data,
            }
        )


class ExpenseReportView(APIView):
    def get(self, request):
        start, end = get_date_range(request)
        expenses = Expense.objects.filter(date__gte=start, date__lte=end)
        expense_type = request.query_params.get("expense_type", "")
        if expense_type:
            expenses = expenses.filter(expense_type=expense_type)
        total = expenses.aggregate(Sum("amount"))["amount__sum"] or 0
        return Response(
            {
                "start": start,
                "end": end,
                "expense_type": expense_type,
                "total": _decimal_text(total),
                "results": ExpenseSerializer(expenses, many=True, context={"request": request}).data,
            }
        )


class PaymentReportView(APIView):
    def get(self, request):
        start, end = get_date_range(request)
        payments = Payment.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
        status_filter = request.query_params.get("status", "")
        if status_filter:
            payments = payments.filter(payment_status=status_filter)
        total_collected = payments.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
        total_due = payments.aggregate(Sum("amount_due"))["amount_due__sum"] or 0
        return Response(
            {
                "start": start,
                "end": end,
                "status": status_filter,
                "total_collected": _decimal_text(total_collected),
                "total_due": _decimal_text(total_due),
                "results": PaymentSerializer(payments, many=True, context={"request": request}).data,
            }
        )


class ProfitLossReportView(APIView):
    def get(self, request):
        start, end = get_date_range(request)
        revenue = Payment.objects.filter(
            payment_date__gte=start,
            payment_date__lte=end,
            payment_status="paid",
        ).aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
        expenses_total = Expense.objects.filter(
            date__gte=start,
            date__lte=end,
        ).aggregate(Sum("amount"))["amount__sum"] or 0
        return Response(
            {
                "start": start,
                "end": end,
                "revenue": _decimal_text(revenue),
                "expenses": _decimal_text(expenses_total),
                "profit": _decimal_text(revenue - expenses_total),
            }
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def unread_notification_count(request):
    return Response({"count": Notification.objects.filter(user=request.user, is_read=False).count()})


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({"unread_count": 0})
