import random
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Profile
from trucks.models import Truck
from drivers.models import Driver
from clients.models import Client
from trips.models import Trip
from cargo.models import Cargo
from expenses.models import Expense
from payments.models import Payment
from maintenance.models import Maintenance
from notifications.models import Notification

User = get_user_model()
PHT = ZoneInfo("Asia/Manila")
random.seed(42)


def peso(minimum, maximum):
    return Decimal(str(round(random.uniform(minimum, maximum), 2)))


def aware_at(day, hour, minute=0):
    return timezone.make_aware(
        datetime.combine(day, datetime.min.time()).replace(hour=hour, minute=minute),
        PHT,
    )


class Command(BaseCommand):
    help = "Clears and seeds sample data (5+ records per model)"

    def handle(self, *args, **options):
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(self.style.ERROR("No superuser found. Run seedadmin first."))
            return

        self.stdout.write("Clearing existing data...")
        Notification.objects.all().delete()
        Payment.objects.all().delete()
        Expense.objects.all().delete()
        Cargo.objects.all().delete()
        Maintenance.objects.all().delete()
        Trip.objects.all().delete()
        Driver.objects.all().delete()
        Client.objects.all().delete()
        Truck.objects.all().delete()

        today = timezone.localdate()

        # ── Trucks ──────────────────────────────────────────────────
        self.stdout.write("Creating trucks...")
        truck_data = [
            ("ABC-1234", "UNIT-01", "box", 5000, 2020, "available"),
            ("XYZ-5678", "UNIT-02", "flatbed", 12000, 2021, "assigned"),
            ("DEF-9012", "UNIT-03", "refrigerated", 8000, 2022, "on_trip"),
            ("GHI-3456", "UNIT-04", "dump", 20000, 2019, "maintenance"),
            ("JKL-7890", "UNIT-05", "container", 25000, 2023, "available"),
            ("MNO-1111", "UNIT-06", "tanker", 15000, 2020, "assigned"),
        ]
        trucks = []
        for plate, unit, ttype, cap, year, status in truck_data:
            t = Truck.objects.create(
                plate_number=plate,
                unit_number=unit,
                truck_type=ttype,
                capacity=cap,
                year_model=year,
                registration_number=f"REG-{plate.replace('-', '')}",
                registration_expiry=today + timedelta(days=random.randint(60, 360)),
                insurance_expiry=today + timedelta(days=random.randint(60, 360)),
                status=status,
                remarks="Sample fleet unit",
            )
            trucks.append(t)

        # ── Drivers ────────────────────────────────────────────────
        self.stdout.write("Creating drivers...")
        driver_data = [
            ("Juan Dela Cruz", "0917-111-1111", "Manila City"),
            ("Maria Santos", "0917-222-2222", "Quezon City"),
            ("Pedro Reyes", "0917-333-3333", "Cebu City"),
            ("Ana Gonzales", "0917-444-4444", "Davao City"),
            ("Jose Mercado", "0917-555-5555", "Iloilo City"),
            ("Luisa Bautista", "0917-666-6666", "Bacolod City"),
        ]
        drivers = []
        for idx, (name, phone, address) in enumerate(driver_data):
            d = Driver.objects.create(
                full_name=name,
                contact_number=phone,
                address=address,
                license_number=f"LIC-{random.randint(100000, 999999)}",
                license_expiry=today + timedelta(days=random.randint(90, 720)),
                assigned_truck=trucks[idx] if idx < len(trucks) else None,
                employment_status="active",
                emergency_contact_name=f"{name.split()[0]} Emergency",
                emergency_contact_number=phone.replace("111", "911"),
                remarks="Sample driver",
            )
            drivers.append(d)

        # ── Clients ────────────────────────────────────────────────
        self.stdout.write("Creating clients...")
        client_data = [
            ("Manila Mega Warehouse", "Alice Tan", "0917-101-0101", "Manila"),
            ("Cebu Pacific Logistics", "Ben Lim", "0917-202-0202", "Cebu City"),
            ("Davao Fresh Produce Inc.", "Cathy Uy", "0917-303-0303", "Davao City"),
            ("North Luzon Hardware", "David Co", "0917-404-0404", "Clark"),
            ("Visayas Cold Storage", "Eva Yu", "0917-505-0505", "Cebu City"),
            ("Mindanao Agri Traders", "Frank Tan", "0917-606-0606", "General Santos"),
        ]
        clients = []
        for name, contact, phone, address in client_data:
            c = Client.objects.create(
                client_name=name,
                contact_person=contact,
                contact_number=phone,
                email=f"{name.lower().replace(' ', '.')}@example.ph",
                address=address,
                company_name=name,
                notes="Sample client",
            )
            clients.append(c)

        # ── Trips + Cargo + Expenses + Payments ────────────────────
        self.stdout.write("Creating trips with cargo, expenses, payments...")
        routes = [
            ("Manila Port", "Quezon City Warehouse", "Electronics"),
            ("Cebu Harbor", "Mandaue Depot", "Furniture"),
            ("Davao Sasa Wharf", "Toril Distribution Center", "Groceries"),
            ("Clark Freeport", "Subic Bay Terminal", "Machinery"),
            ("Bacolod City", "Iloilo City Port", "Sugar"),
            ("General Santos", "Davao City Market", "Fish"),
        ]
        trips = []
        for idx, (pickup, dropoff, cargo_desc) in enumerate(routes):
            day = today - timedelta(days=30 - idx * 5)
            pickup_time = aware_at(day, random.choice([6, 8, 10]))
            delivery_time = pickup_time + timedelta(hours=random.choice([4, 8, 24]))
            status = ["delivered", "in_transit", "scheduled", "delivered", "loading", "pending"][idx]
            actual_pickup = pickup_time + timedelta(minutes=30) if status in ["loading", "in_transit", "delivered"] else None
            actual_delivery = delivery_time + timedelta(minutes=45) if status == "delivered" else None

            trip = Trip.objects.create(
                reference_number=f"SMP-{today.strftime('%Y%m')}-{idx + 1:04d}",
                client=clients[idx % len(clients)],
                assigned_truck=trucks[idx % len(trucks)],
                assigned_driver=drivers[idx % len(drivers)],
                pickup_location=pickup,
                dropoff_location=dropoff,
                cargo_description=cargo_desc,
                cargo_weight=peso(500, 20000),
                cargo_quantity=random.randint(10, 200),
                scheduled_pickup=pickup_time,
                scheduled_delivery=delivery_time,
                actual_pickup=actual_pickup,
                actual_delivery=actual_delivery,
                status=status,
                remarks="Sample trip",
                created_by=admin,
            )
            trips.append(trip)

            Cargo.objects.create(
                trip=trip,
                cargo_type=cargo_desc,
                description=f"{cargo_desc} for {trip.client.client_name}",
                weight=trip.cargo_weight,
                quantity=trip.cargo_quantity,
                special_handling="Handle with care",
                condition_before="excellent",
                condition_after="good" if status == "delivered" else None,
            )

            for etype in ["fuel", random.choice(["toll", "parking", "allowance"])]:
                Expense.objects.create(
                    trip=trip,
                    truck=trip.assigned_truck,
                    expense_type=etype,
                    amount=peso(300, 8000),
                    date=day,
                    notes=f"{etype.title()} for {trip.reference_number}",
                )

            amount_due = peso(10000, 150000)
            amount_paid = (
                amount_due
                if status == "delivered" and idx % 3 != 0
                else (amount_due * Decimal("0.50")).quantize(Decimal("0.01"))
            )
            if status in ["pending", "scheduled"] and idx % 2 == 0:
                amount_paid = Decimal("0.00")
            Payment.objects.create(
                trip=trip,
                client=trip.client,
                amount_due=amount_due,
                amount_paid=amount_paid,
                payment_date=day + timedelta(days=random.randint(1, 12)) if amount_paid > 0 else None,
                payment_method=random.choice(["Bank Transfer", "Cash", "Check", "GCash"]) if amount_paid > 0 else None,
                notes=f"Payment for {trip.reference_number}",
            )

        # ── Maintenance ────────────────────────────────────────────
        self.stdout.write("Creating maintenance records...")
        mtypes = ["routine", "oil_change", "tire", "brake", "engine", "transmission"]
        for idx, truck in enumerate(trucks):
            service_day = today - timedelta(days=random.randint(1, 90))
            Maintenance.objects.create(
                truck=truck,
                maintenance_type=mtypes[idx % len(mtypes)],
                description=f"{mtypes[idx % len(mtypes)].replace('_', ' ').title()} for {truck.plate_number}",
                service_date=service_day,
                next_service_date=service_day + timedelta(days=random.choice([30, 60, 90])),
                cost=peso(1500, 40000),
                service_provider=random.choice([
                    "AutoCare Center", "TruckFix Pro", "Mega Fleet Service", "QuickLube",
                ]),
                status=random.choice(["completed", "completed", "scheduled", "ongoing"]),
                remarks="Sample maintenance",
            )

        # ── Notifications ──────────────────────────────────────────
        self.stdout.write("Creating notifications...")
        notif_data = [
            ("trip_assigned", "New trip assigned", "A new trip has been assigned to a driver."),
            ("trip_completed", "Trip completed", "A delivery has been marked as delivered."),
            ("maintenance_due", "Maintenance due", "A truck has upcoming maintenance."),
            ("payment_overdue", "Payment overdue", "A client payment is past due."),
            ("insurance_expiry", "Insurance expiring", "A truck insurance policy is about to expire."),
            ("license_expiry", "License expiring", "A driver's license is nearing expiry."),
        ]
        for ntype, title, msg in notif_data:
            Notification.objects.create(
                user=admin,
                notification_type=ntype,
                title=title,
                message=msg,
                link="/dashboard/",
                is_read=False,
            )

        # ── Summary ────────────────────────────────────────────────
        self.stdout.write()
        self.stdout.write("=" * 50)
        self.stdout.write("Sample data seeding complete")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Users:         {User.objects.count()}")
        self.stdout.write(f"Trucks:        {Truck.objects.count()}")
        self.stdout.write(f"Drivers:       {Driver.objects.count()}")
        self.stdout.write(f"Clients:       {Client.objects.count()}")
        self.stdout.write(f"Trips:         {Trip.objects.count()}")
        self.stdout.write(f"Cargo items:   {Cargo.objects.count()}")
        self.stdout.write(f"Maintenance:   {Maintenance.objects.count()}")
        self.stdout.write(f"Expenses:      {Expense.objects.count()}")
        self.stdout.write(f"Payments:      {Payment.objects.count()}")
        self.stdout.write(f"Notifications: {Notification.objects.count()}")
        self.stdout.write()
        self.stdout.write(self.style.SUCCESS("Done!"))
