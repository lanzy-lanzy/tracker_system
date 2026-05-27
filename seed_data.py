import os
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tracker_system.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django

django.setup()

from django.contrib.auth.models import User
from django.utils import timezone

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

PHT = ZoneInfo("Asia/Manila")
random.seed(20260522)

ADMIN_USERNAME = os.environ.get("SEED_ADMIN_USERNAME", "admin")
ADMIN_EMAIL = os.environ.get("SEED_ADMIN_EMAIL", "admin@fast-track.local")
ADMIN_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD")
STAFF_PASSWORD = os.environ.get("SEED_STAFF_PASSWORD", ADMIN_PASSWORD)

if not ADMIN_PASSWORD:
    raise RuntimeError("Set SEED_ADMIN_PASSWORD before running this script.")


def peso(minimum, maximum):
    return Decimal(str(round(random.uniform(minimum, maximum), 2)))


def aware_at(day, hour, minute=0):
    return timezone.make_aware(datetime.combine(day, datetime.min.time()).replace(hour=hour, minute=minute), PHT)


print("Seeding Davao City demo data...")
print("Clearing existing operational data...")
Notification.objects.all().delete()
Payment.objects.all().delete()
Expense.objects.all().delete()
Cargo.objects.all().delete()
Maintenance.objects.all().delete()
Trip.objects.all().delete()
Driver.objects.all().delete()
Client.objects.all().delete()
Truck.objects.all().delete()
Profile.objects.filter(user__username__in=["dispatcher.davao", "staff.davao"]).delete()
User.objects.filter(username__in=["dispatcher.davao", "staff.davao"]).delete()

today = timezone.localdate()

print("Creating admin and staff users...")
admin, _ = User.objects.update_or_create(
    username=ADMIN_USERNAME,
    defaults={
        "email": ADMIN_EMAIL,
        "first_name": "Fast Track",
        "last_name": "Admin",
        "is_staff": True,
        "is_superuser": True,
        "is_active": True,
    },
)
admin.set_password(ADMIN_PASSWORD)
admin.save()
Profile.objects.update_or_create(
    user=admin,
    defaults={
        "role": "admin",
        "phone": "0917-800-2026",
        "address": "Poblacion District, Davao City",
    },
)

staff_users = [
    ("dispatcher.davao", "Mika", "Santos", "dispatcher", "0917-810-1001"),
    ("staff.davao", "Carlo", "Dizon", "driver", "0917-810-1002"),
]
for username, first_name, last_name, role, phone in staff_users:
    user, _ = User.objects.update_or_create(
        username=username,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{username}@fast-track.local",
            "is_active": True,
        },
    )
    user.set_password(STAFF_PASSWORD)
    user.save()
    Profile.objects.update_or_create(
        user=user,
        defaults={
            "role": role,
            "phone": phone,
            "address": "Davao City, Davao del Sur",
        },
    )

print("Creating Davao fleet...")
truck_data = [
    ("LAA-2481", "DC-BOX-01", "box", 6500, 2021, "assigned"),
    ("MAA-7315", "DC-FLT-02", "flatbed", 14000, 2020, "on_trip"),
    ("NAB-9024", "DC-REF-03", "refrigerated", 9000, 2022, "available"),
    ("KAD-5188", "DC-DMP-04", "dump", 18000, 2019, "maintenance"),
    ("MAB-4407", "DC-CNT-05", "container", 21000, 2023, "assigned"),
    ("LAC-6720", "DC-TNK-06", "tanker", 12000, 2020, "available"),
    ("NAE-1169", "DC-BOX-07", "box", 7500, 2022, "assigned"),
    ("KAF-8842", "DC-FLT-08", "flatbed", 16000, 2021, "available"),
    ("MAL-3056", "DC-REF-09", "refrigerated", 10000, 2023, "on_trip"),
    ("NAG-7912", "DC-CNT-10", "container", 19000, 2022, "available"),
]
trucks = []
for plate, unit, truck_type, capacity, year, status in truck_data:
    truck, _ = Truck.objects.update_or_create(
        plate_number=plate,
        defaults={
            "unit_number": unit,
            "truck_type": truck_type,
            "capacity": capacity,
            "year_model": year,
            "registration_number": f"LTFRB-XI-{plate.replace('-', '')}",
            "registration_expiry": today + timedelta(days=random.randint(45, 320)),
            "insurance_expiry": today + timedelta(days=random.randint(60, 360)),
            "status": status,
            "remarks": "Davao hub demo fleet unit",
        },
    )
    trucks.append(truck)

print("Creating drivers...")
driver_data = [
    ("Rodel Ampatuan", "0917-821-3301", "Buhangin, Davao City"),
    ("Jessa Caballero", "0917-821-3302", "Matina Crossing, Davao City"),
    ("Mark Villarin", "0917-821-3303", "Toril, Davao City"),
    ("Nico Fernandez", "0917-821-3304", "Calinan, Davao City"),
    ("Alvin Lumantas", "0917-821-3305", "Panacan, Davao City"),
    ("Grace Montejo", "0917-821-3306", "Mintal, Davao City"),
    ("Dante Esguerra", "0917-821-3307", "Bunawan, Davao City"),
    ("Ian Delos Reyes", "0917-821-3308", "Tugbok, Davao City"),
    ("Paolo Macaraeg", "0917-821-3309", "Lanang, Davao City"),
    ("Lara Abella", "0917-821-3310", "Talomo, Davao City"),
]
drivers = []
for index, (name, phone, address) in enumerate(driver_data):
    driver, _ = Driver.objects.update_or_create(
        full_name=name,
        defaults={
            "contact_number": phone,
            "address": address,
            "license_number": f"DVO-{random.randint(100000, 999999)}",
            "license_expiry": today + timedelta(days=random.randint(90, 720)),
            "assigned_truck": trucks[index] if index < 8 else None,
            "employment_status": "active",
            "emergency_contact_name": f"{name.split()[0]} Emergency Contact",
            "emergency_contact_number": phone.replace("821", "822"),
            "remarks": "Davao route certified",
        },
    )
    drivers.append(driver)

print("Creating clients...")
client_data = [
    ("Davao Central Warehouse", "Elena Mercado", "0917-841-2201", "Bajada, Davao City"),
    ("Toril Agri Supply Cooperative", "Jun Paredes", "0917-841-2202", "Toril, Davao City"),
    ("Panacan Cold Storage", "Rhea Lim", "0917-841-2203", "Panacan, Davao City"),
    ("Buhangin Hardware Depot", "Arnold Tan", "0917-841-2204", "Buhangin, Davao City"),
    ("Matina Food Distributors", "Cora Uy", "0917-841-2205", "Matina, Davao City"),
    ("Calinan Fruit Growers", "Marlon Abad", "0917-841-2206", "Calinan, Davao City"),
    ("Sasa Port Logistics", "Victor Yu", "0917-841-2207", "Sasa, Davao City"),
    ("Lanang Medical Supplies", "Dr. Hannah Cruz", "0917-841-2208", "Lanang, Davao City"),
    ("Tagum Retail Consolidators", "Mae Soriano", "0917-841-2209", "Tagum City, Davao del Norte"),
    ("Digos Construction Mart", "Oscar Marquez", "0917-841-2210", "Digos City, Davao del Sur"),
]
clients = []
for name, contact, phone, address in client_data:
    client, _ = Client.objects.update_or_create(
        client_name=name,
        defaults={
            "contact_person": contact,
            "contact_number": phone,
            "email": f"{name.lower().replace(' ', '.')}@example.ph",
            "address": address,
            "company_name": name,
            "notes": "Seeded Davao Region customer",
        },
    )
    clients.append(client)

print("Creating trips, cargo, expenses, and payments...")
routes = [
    ("Sasa Port, Davao City", "Bajada, Davao City", "Imported dry goods"),
    ("Panacan Cold Storage, Davao City", "Matina, Davao City", "Frozen seafood and meat"),
    ("Toril Public Market, Davao City", "Mintal, Davao City", "Fresh produce"),
    ("Calinan, Davao City", "Bankerohan Public Market, Davao City", "Bananas and assorted fruit"),
    ("Buhangin, Davao City", "Lanang, Davao City", "Hardware and cement bags"),
    ("Davao City Overland Transport Terminal", "Digos City, Davao del Sur", "Retail merchandise"),
    ("Davao Fish Port Complex", "Tagum City, Davao del Norte", "Chilled fish boxes"),
    ("Sasa Wharf, Davao City", "Toril, Davao City", "Containerized grocery items"),
    ("Lanang, Davao City", "Island Garden City of Samal", "Medical supplies"),
    ("Tugbok, Davao City", "Bansalan, Davao del Sur", "Farm inputs"),
    ("Bunawan, Davao City", "Panabo City, Davao del Norte", "Warehouse pallets"),
    ("Matina Crossing, Davao City", "Kidapawan City, Cotabato", "Office fixtures"),
    ("Davao International Airport Cargo", "Poblacion District, Davao City", "Express parcels"),
    ("Maa, Davao City", "Toril, Davao City", "School supplies"),
    ("Agdao, Davao City", "Davao del Sur Provincial Capitol, Digos", "Government office supplies"),
    ("Calinan, Davao City", "Mati City, Davao Oriental", "Fruit crates"),
    ("Sasa Port, Davao City", "General Santos City", "Fishery equipment"),
    ("Bajada, Davao City", "Davao Doctors Hospital Area", "Medical equipment"),
]
statuses = ["delivered", "in_transit", "scheduled", "delivered", "loading", "pending"]
trips = []
for index, (pickup, dropoff, cargo_description) in enumerate(routes):
    day = today - timedelta(days=40 - index * 2)
    pickup_time = aware_at(day, random.choice([6, 7, 8, 9, 13]))
    delivery_time = pickup_time + timedelta(hours=random.choice([3, 5, 8, 18, 30]))
    status = statuses[index % len(statuses)]
    actual_pickup = pickup_time + timedelta(minutes=random.choice([15, 30, 45])) if status in ["loading", "in_transit", "delivered"] else None
    actual_delivery = delivery_time + timedelta(minutes=random.choice([10, 35, 70])) if status == "delivered" else None
    trip, _ = Trip.objects.update_or_create(
        reference_number=f"DVO-{today.strftime('%Y%m')}-{index + 1:04d}",
        defaults={
            "client": clients[index % len(clients)],
            "assigned_truck": trucks[index % len(trucks)],
            "assigned_driver": drivers[index % len(drivers)],
            "pickup_location": pickup,
            "dropoff_location": dropoff,
            "cargo_description": cargo_description,
            "cargo_weight": peso(450, 14500),
            "cargo_quantity": random.randint(8, 180),
            "scheduled_pickup": pickup_time,
            "scheduled_delivery": delivery_time,
            "actual_pickup": actual_pickup,
            "actual_delivery": actual_delivery,
            "status": status,
            "remarks": "Davao Region demo route",
            "created_by": admin,
        },
    )
    trips.append(trip)

    Cargo.objects.update_or_create(
        trip=trip,
        cargo_type=cargo_description.split()[0],
        defaults={
            "description": f"{cargo_description} for {trip.client.client_name}",
            "weight": trip.cargo_weight,
            "quantity": trip.cargo_quantity,
            "special_handling": "Keep dry and verify receiving documents",
            "condition_before": "excellent",
            "condition_after": "good" if status == "delivered" else None,
        },
    )

    for expense_type in ["fuel", random.choice(["toll", "parking", "allowance"])]:
        Expense.objects.update_or_create(
            trip=trip,
            truck=trip.assigned_truck,
            expense_type=expense_type,
            date=day,
            defaults={
                "amount": peso(250, 9500),
                "notes": f"{expense_type.title()} expense for {trip.reference_number}",
            },
        )

    amount_due = peso(8500, 125000)
    amount_paid = amount_due if status == "delivered" and index % 3 != 0 else (amount_due * Decimal("0.45")).quantize(Decimal("0.01"))
    if status in ["pending", "scheduled"] and index % 2 == 0:
        amount_paid = Decimal("0.00")
    Payment.objects.update_or_create(
        trip=trip,
        client=trip.client,
        defaults={
            "amount_due": amount_due,
            "amount_paid": amount_paid,
            "payment_date": day + timedelta(days=random.randint(1, 12)) if amount_paid > 0 else None,
            "payment_method": random.choice(["Bank Transfer", "Cash", "Check", "GCash"]) if amount_paid > 0 else None,
            "notes": f"Billing for {trip.reference_number}",
        },
    )

print("Creating maintenance records...")
maintenance_types = ["routine", "oil_change", "tire", "brake", "engine", "transmission", "electrical", "other"]
for index, truck in enumerate(trucks[:12]):
    service_day = today - timedelta(days=random.randint(2, 85))
    Maintenance.objects.update_or_create(
        truck=truck,
        maintenance_type=maintenance_types[index % len(maintenance_types)],
        service_date=service_day,
        defaults={
            "description": f"{maintenance_types[index % len(maintenance_types)].replace('_', ' ').title()} service for {truck.plate_number}",
            "next_service_date": service_day + timedelta(days=random.choice([30, 60, 90])),
            "cost": peso(1800, 38000),
            "service_provider": random.choice(["Davao Diesel Works", "Matina Truck Care", "Panacan Fleet Service", "Buhangin Auto Center"]),
            "status": random.choice(["completed", "scheduled", "ongoing"]),
            "remarks": "Davao fleet maintenance demo record",
        },
    )

print("Creating notifications...")
notifications = [
    ("trip_assigned", "DVO trip assigned", "A Davao route has been assigned to a driver."),
    ("trip_completed", "Delivery completed", "A delivery within Davao City was marked delivered."),
    ("maintenance_due", "Maintenance due", "One fleet unit has upcoming preventive maintenance."),
    ("payment_overdue", "Payment follow-up", "A partially paid Davao delivery needs collection follow-up."),
    ("insurance_expiry", "Insurance reminder", "A vehicle insurance policy is nearing expiry."),
]
for notification_type, title, message in notifications:
    Notification.objects.update_or_create(
        user=admin,
        notification_type=notification_type,
        title=title,
        defaults={"message": message, "link": "/dashboard/", "is_read": False},
    )

print()
print("=" * 50)
print("Davao demo data seeding complete")
print("=" * 50)
print(f"Users:         {User.objects.count()}")
print(f"Trucks:        {Truck.objects.count()}")
print(f"Drivers:       {Driver.objects.count()}")
print(f"Clients:       {Client.objects.count()}")
print(f"Trips:         {Trip.objects.count()}")
print(f"Cargo items:   {Cargo.objects.count()}")
print(f"Maintenance:   {Maintenance.objects.count()}")
print(f"Expenses:      {Expense.objects.count()}")
print(f"Payments:      {Payment.objects.count()}")
print(f"Notifications: {Notification.objects.count()}")
print()
print("Login users:")
print(f"Admin:      {ADMIN_USERNAME}")
print("Dispatcher: dispatcher.davao")
print("Staff:      staff.davao")
