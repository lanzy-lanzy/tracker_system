from django.contrib.auth.models import User
from rest_framework import serializers

from accounts.models import Profile
from cargo.models import Cargo
from clients.models import Client
from drivers.models import Driver
from expenses.models import Expense
from maintenance.models import Maintenance
from notifications.models import Notification
from payments.models import Payment
from trips.models import Trip
from trucks.models import Truck


class ProfileSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "role",
            "role_display",
            "phone",
            "address",
            "profile_picture",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_active", "profile"]


class ClientSerializer(serializers.ModelSerializer):
    total_outstanding = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Client
        fields = [
            "id",
            "client_name",
            "contact_person",
            "contact_number",
            "email",
            "address",
            "company_name",
            "notes",
            "total_outstanding",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class TruckSerializer(serializers.ModelSerializer):
    truck_type_display = serializers.CharField(source="get_truck_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    registration_expired = serializers.BooleanField(source="is_registration_expired", read_only=True)
    insurance_expired = serializers.BooleanField(source="is_insurance_expired", read_only=True)
    days_until_registration_expiry = serializers.IntegerField(read_only=True)
    days_until_insurance_expiry = serializers.IntegerField(read_only=True)

    class Meta:
        model = Truck
        fields = [
            "id",
            "plate_number",
            "unit_number",
            "truck_type",
            "truck_type_display",
            "capacity",
            "year_model",
            "registration_number",
            "registration_expiry",
            "insurance_expiry",
            "status",
            "status_display",
            "remarks",
            "registration_expired",
            "insurance_expired",
            "days_until_registration_expiry",
            "days_until_insurance_expiry",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class DriverSerializer(serializers.ModelSerializer):
    employment_status_display = serializers.CharField(source="get_employment_status_display", read_only=True)
    assigned_truck_plate = serializers.CharField(source="assigned_truck.plate_number", read_only=True)
    license_expired = serializers.BooleanField(source="is_license_expired", read_only=True)
    days_until_license_expiry = serializers.IntegerField(read_only=True)

    class Meta:
        model = Driver
        fields = [
            "id",
            "user",
            "full_name",
            "contact_number",
            "address",
            "license_number",
            "license_expiry",
            "assigned_truck",
            "assigned_truck_plate",
            "employment_status",
            "employment_status_display",
            "emergency_contact_name",
            "emergency_contact_number",
            "remarks",
            "license_expired",
            "days_until_license_expiry",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class TripSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    client_name = serializers.CharField(source="client.client_name", read_only=True)
    assigned_truck_plate = serializers.CharField(source="assigned_truck.plate_number", read_only=True)
    assigned_driver_name = serializers.CharField(source="assigned_driver.full_name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    duration_hours = serializers.FloatField(read_only=True)

    class Meta:
        model = Trip
        fields = [
            "id",
            "reference_number",
            "client",
            "client_name",
            "assigned_truck",
            "assigned_truck_plate",
            "assigned_driver",
            "assigned_driver_name",
            "pickup_location",
            "dropoff_location",
            "cargo_description",
            "cargo_weight",
            "cargo_quantity",
            "scheduled_pickup",
            "scheduled_delivery",
            "actual_pickup",
            "actual_delivery",
            "status",
            "status_display",
            "delivery_proof",
            "remarks",
            "created_by",
            "created_by_username",
            "is_overdue",
            "duration_hours",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["reference_number", "created_by", "created_at", "updated_at"]


class CargoSerializer(serializers.ModelSerializer):
    trip_reference = serializers.CharField(source="trip.reference_number", read_only=True)
    condition_before_display = serializers.CharField(source="get_condition_before_display", read_only=True)
    condition_after_display = serializers.CharField(source="get_condition_after_display", read_only=True)

    class Meta:
        model = Cargo
        fields = [
            "id",
            "trip",
            "trip_reference",
            "cargo_type",
            "description",
            "weight",
            "quantity",
            "special_handling",
            "condition_before",
            "condition_before_display",
            "condition_after",
            "condition_after_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class MaintenanceSerializer(serializers.ModelSerializer):
    truck_plate = serializers.CharField(source="truck.plate_number", read_only=True)
    maintenance_type_display = serializers.CharField(source="get_maintenance_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    overdue = serializers.BooleanField(source="is_overdue", read_only=True)
    days_until_due = serializers.IntegerField(read_only=True)

    class Meta:
        model = Maintenance
        fields = [
            "id",
            "truck",
            "truck_plate",
            "maintenance_type",
            "maintenance_type_display",
            "description",
            "service_date",
            "next_service_date",
            "cost",
            "service_provider",
            "status",
            "status_display",
            "remarks",
            "overdue",
            "days_until_due",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ExpenseSerializer(serializers.ModelSerializer):
    trip_reference = serializers.CharField(source="trip.reference_number", read_only=True)
    truck_plate = serializers.CharField(source="truck.plate_number", read_only=True)
    expense_type_display = serializers.CharField(source="get_expense_type_display", read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id",
            "trip",
            "trip_reference",
            "truck",
            "truck_plate",
            "expense_type",
            "expense_type_display",
            "amount",
            "date",
            "receipt",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class PaymentSerializer(serializers.ModelSerializer):
    trip_reference = serializers.CharField(source="trip.reference_number", read_only=True)
    client_name = serializers.CharField(source="client.client_name", read_only=True)
    payment_status_display = serializers.CharField(source="get_payment_status_display", read_only=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "trip",
            "trip_reference",
            "client",
            "client_name",
            "amount_due",
            "amount_paid",
            "balance",
            "payment_status",
            "payment_status_display",
            "payment_date",
            "payment_method",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["payment_status", "created_at", "updated_at"]


class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(source="get_notification_type_display", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "notification_type",
            "notification_type_display",
            "title",
            "message",
            "link",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["created_at"]
