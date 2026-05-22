import os, sys, random
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo

os.environ["DJANGO_SETTINGS_MODULE"] = "tracker_system.settings"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django; django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import Profile
from trucks.models import Truck
from drivers.models import Driver
from clients.models import Client
from trips.models import Trip
from cargo.models import Cargo
from maintenance.models import Maintenance
from expenses.models import Expense
from payments.models import Payment
from notifications.models import Notification

PHT = ZoneInfo("Asia/Manila")

print("Seeding data...")

# --- Clean existing data (optional, comment out to keep) ---
print("Clearing existing data...")
Notification.objects.all().delete()
Payment.objects.all().delete()
Expense.objects.all().delete()
Cargo.objects.all().delete()
Maintenance.objects.all().delete()
Trip.objects.all().delete()
Driver.objects.all().delete()
Client.objects.all().delete()
Truck.objects.all().delete()
Profile.objects.filter(user__username__in=["dispatcher1", "staff1"]).delete()
User.objects.filter(username__in=["dispatcher1", "staff1"]).delete()

today = timezone.now().date()

# ============================================================
# USERS
# ============================================================
print("Creating users...")
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "admin@tracker.com", "admin123")

for uname, fname, lname, role in [
    ("dispatcher1", "Maria", "Santos", "dispatcher"),
    ("staff1", "Juan", "Cruz", "driver"),
]:
    u, created = User.objects.get_or_create(username=uname, defaults={
        "first_name": fname, "last_name": lname, "email": f"{uname}@tracker.com"
    })
    if created:
        u.set_password("password123")
        u.save()
        Profile.objects.filter(user=u).update(role=role)
        print(f"  Created user: {uname}")
    else:
        Profile.objects.filter(user=u).update(role=role)
        print(f"  User exists: {uname}")

# ============================================================
# TRUCKS (10)
# ============================================================
print("Creating trucks...")
truck_data = [
    ("ABC-1234", "FL-001", "flatbed", 15000, 2020),
    ("XYZ-5678", "BX-002", "box", 8000, 2021),
    ("DEF-9012", "RF-003", "refrigerated", 10000, 2022),
    ("GHI-3456", "TN-004", "tanker", 12000, 2019),
    ("JKL-7890", "DM-005", "dump", 20000, 2020),
    ("MNO-2345", "CT-006", "container", 18000, 2023),
    ("PQR-6789", "FL-007", "flatbed", 16000, 2021),
    ("STU-0123", "BX-008", "box", 7500, 2022),
    ("VWX-4567", "RF-009", "refrigerated", 11000, 2023),
    ("YZA-8901", "FL-010", "flatbed", 14000, 2020),
]
trucks = []
for pn, un, tt, cap, yr in truck_data:
    t, _ = Truck.objects.get_or_create(plate_number=pn, defaults={
        "unit_number": un, "truck_type": tt, "capacity": cap,
        "year_model": yr, "status": "available",
        "registration_expiry": today + timedelta(days=random.randint(30, 365)),
        "insurance_expiry": today + timedelta(days=random.randint(30, 365)),
    })
    trucks.append(t)
print(f"  {len(trucks)} trucks ready")

# ============================================================
# DRIVERS (10)
# ============================================================
print("Creating drivers...")
driver_names = [
    ("Carlos", "Reyes", "09171234567"),
    ("Ana", "Gomez", "09179876543"),
    ("Pedro", "Villanueva", "09175678901"),
    ("Liza", "Mendoza", "09172345678"),
    ("Ramon", "Fernandez", "09178901234"),
    ("Sofia", "Lopez", "09174567890"),
    ("Mario", "Torres", "09173456789"),
    ("Elena", "Cruz", "09179012345"),
    ("Jose", "Rivera", "09175612345"),
    ("Kris", "Santos", "09177890123"),
]
drivers = []
for fn, ln, cn in driver_names:
    full = f"{fn} {ln}"
    idx = driver_names.index((fn, ln, cn))
    d, _ = Driver.objects.get_or_create(full_name=full, defaults={
        "contact_number": cn,
        "license_number": f"L-{random.randint(10000,99999)}",
        "license_expiry": today + timedelta(days=random.randint(60, 365)),
        "employment_status": "active",
        "assigned_truck": random.choice(trucks) if idx < 8 else None,
    })
    drivers.append(d)
print(f"  {len(drivers)} drivers ready")

# ============================================================
# CLIENTS (10)
# ============================================================
print("Creating clients...")
client_data = [
    ("Metro Freight Solutions", "Jose Rizal", "09171234501", "metro@email.com"),
    ("Luzon Logistics Inc.", "Maria Clara", "09179876502", "luzon@email.com"),
    ("VisMin Transport", "Andres Bonifacio", "09175678903", "vismin@email.com"),
    ("Northern Cargo Corp.", "Emilio Aguinaldo", "09172345604", "northern@email.com"),
    ("Southern Haulers", "Gabriela Silang", "09178901205", "southern@email.com"),
    ("East Express Co.", "Lapu-Lapu", "09174567806", "east@email.com"),
    ("West Wing Logistics", "Melchora Aquino", "09173456707", "west@email.com"),
    ("Island Shipping Corp.", "Antonio Luna", "09179012308", "island@email.com"),
    ("Central Distributors", "Josefa Llanes", "09175612309", "central@email.com"),
    ("Prime Movers Inc.", "Marcelo del Pilar", "09177890110", "prime@email.com"),
]
clients = []
for cn, cp, cnum, em in client_data:
    c, _ = Client.objects.get_or_create(client_name=cn, defaults={
        "contact_person": cp, "contact_number": cnum, "email": em,
        "company_name": cn,
    })
    clients.append(c)
print(f"  {len(clients)} clients ready")

# ============================================================
# TRIPS (15)
# ============================================================
print("Creating trips...")
statuses = ["pending", "scheduled", "loading", "in_transit", "delivered", "cancelled"]
locations = [
    ("Quezon City, NCR", "Makati City, NCR"),
    ("Manila Port Area", "Batangas Port"),
    ("Clark, Pampanga", "Dau, Pampanga"),
    ("Baguio City", "La Trinidad, Benguet"),
    ("Dagupan City", "San Fernando, La Union"),
    ("Cabanatuan City", "Tarlac City"),
    ("Olongapo City", "Subic Bay Freeport"),
    ("Lucena City", "Batangas City"),
    ("Calamba, Laguna", "Sta. Rosa, Laguna"),
    ("Cavite City", "Dasmarinas, Cavite"),
    ("Binan, Laguna", "San Pedro, Laguna"),
    ("Imus, Cavite", "General Trias, Cavite"),
    ("Navotas City", "Valenzuela City"),
    ("Cainta, Rizal", "Antipolo City"),
    ("Pasig City", "Mandaluyong City"),
]
descriptions = [
    "General merchandise and dry goods", "Construction materials",
    "Electronics and appliances", "Food and beverage supplies",
    "Medical supplies and equipment", "Agricultural products",
    "Steel and metal parts", "Packaged consumer goods",
    "Industrial chemicals (non-hazardous)", "Textiles and garments",
    "Furniture and fixtures", "Office supplies",
    "Spare parts and machinery", "Frozen food items",
    "Building supplies and hardware",
]
trips = []
for i in range(15):
    client = random.choice(clients)
    truck = random.choice(trucks)
    driver = random.choice(drivers)
    pkup, drop = locations[i]
    days_ago = random.randint(1, 60)
    sch_pickup = timezone.make_aware(
        datetime.combine(today - timedelta(days=days_ago), datetime.min.time()) + timedelta(hours=random.randint(6, 18)),
        PHT,
    )
    sch_delivery = sch_pickup + timedelta(days=random.randint(1, 5))
    t, _ = Trip.objects.get_or_create(
        reference_number=f"TRIP-{(today - timedelta(days=i)).strftime('%Y%m%d')}-{i+1:04d}",
        defaults={
            "client": client,
            "assigned_truck": truck,
            "assigned_driver": driver,
            "pickup_location": pkup,
            "dropoff_location": drop,
            "cargo_description": descriptions[i],
            "cargo_weight": round(random.uniform(500, 12000), 2),
            "cargo_quantity": random.randint(1, 50),
            "scheduled_pickup": sch_pickup,
            "scheduled_delivery": sch_delivery,
            "actual_pickup": sch_pickup + timedelta(hours=1) if i < 12 else None,
            "actual_delivery": sch_delivery + timedelta(hours=random.randint(1, 6)) if i < 10 else None,
            "status": statuses[i % len(statuses)],
        }
    )
    trips.append(t)
print(f"  {len(trips)} trips ready")

# ============================================================
# CARGO (15)
# ============================================================
print("Creating cargo items...")
cargo_types = ["Electronics", "Furniture", "Food", "Construction", "Medical",
               "Clothing", "Machinery", "Chemicals", "Papers", "Metal",
               "Plastic", "Rubber", "Glass", "Wood", "Ceramic"]
for i, t in enumerate(trips[:15]):
    Cargo.objects.get_or_create(
        trip=t, cargo_type=cargo_types[i],
        defaults={
            "description": f"{cargo_types[i]} shipment for {t.client.client_name}",
            "weight": round(random.uniform(100, 8000), 2),
            "quantity": random.randint(5, 100),
            "condition_before": "excellent",
            "condition_after": random.choice(["excellent", "good", "good", "excellent"]),
        }
    )
print(f"  {len(trips)} cargo items ready")

# ============================================================
# MAINTENANCE (12)
# ============================================================
print("Creating maintenance records...")
maintenance_types = ["routine", "oil_change", "tire", "brake", "engine", "transmission",
                     "routine", "oil_change", "electrical", "routine", "brake", "other"]
maint_statuses = ["completed", "completed", "ongoing", "scheduled"]
for i in range(12):
    truck = trucks[i % len(trucks)]
    svc_date = today - timedelta(days=random.randint(1, 90))
    cost = round(random.uniform(1500, 25000), 2) if i % 3 != 3 else None
    Maintenance.objects.get_or_create(
        truck=truck, maintenance_type=maintenance_types[i],
        service_date=svc_date,
        defaults={
            "description": f"{maintenance_types[i].replace('_', ' ').title()} on {truck.plate_number}",
            "cost": cost,
            "service_provider": random.choice(["AutoCare Center", "Truck Masters", "Diesel Pro", "Fleet Services"]),
            "status": maint_statuses[i % len(maint_statuses)],
            "next_service_date": svc_date + timedelta(days=random.choice([30, 60, 90])),
        }
    )
print(f"  12 maintenance records ready")

# ============================================================
# EXPENSES (15)
# ============================================================
print("Creating expenses...")
expense_types = ["fuel", "toll", "repair", "allowance", "parking", "other", "fuel", "toll"]
for i in range(15):
    trip = trips[i % len(trips)]
    truck = trip.assigned_truck or random.choice(trucks)
    exp_date = today - timedelta(days=random.randint(1, 60))
    Expense.objects.get_or_create(
        trip=trip, expense_type=expense_types[i % len(expense_types)],
        date=exp_date, amount=round(random.uniform(200, 15000), 2),
        defaults={
            "truck": truck,
            "notes": f"{expense_types[i % len(expense_types)].title()} expense for trip {trip.reference_number}",
        }
    )
print(f"  15 expenses ready")

# ============================================================
# PAYMENTS (15)
# ============================================================
print("Creating payments...")
pay_statuses = ["paid", "paid", "partial", "unpaid"]
pay_methods = ["Bank Transfer", "Cash", "Check", "GCash", "PayMaya"]
for i in range(15):
    trip = trips[i % len(trips)]
    client = trip.client
    amt_due = round(random.uniform(10000, 150000), 2)
    if pay_statuses[i % 4] == "paid":
        amt_paid = amt_due
    elif pay_statuses[i % 4] == "partial":
        amt_paid = round(amt_due * random.uniform(0.3, 0.7), 2)
    else:
        amt_paid = 0
    pmt_date = today - timedelta(days=random.randint(1, 60)) if amt_paid > 0 else None
    Payment.objects.get_or_create(
        trip=trip, client=client, amount_due=amt_due,
        defaults={
            "amount_paid": amt_paid,
            "payment_date": pmt_date,
            "payment_method": random.choice(pay_methods) if pmt_date else None,
            "notes": f"Payment for trip {trip.reference_number}",
        }
    )
print(f"  15 payments ready")

# ============================================================
# NOTIFICATIONS (10)
# ============================================================
print("Creating notifications...")
admin_user = User.objects.get(username="admin")
notifications_data = [
    ("trip_assigned", "Trip #TR-001 assigned to Carlos Reyes"),
    ("trip_completed", "Trip #TR-002 delivered successfully"),
    ("maintenance_due", "ABC-1234 oil change due in 3 days"),
    ("payment_overdue", "Metro Freight invoice #INV-101 overdue"),
    ("insurance_expiry", "XYZ-5678 insurance expiring next week"),
    ("trip_assigned", "Trip #TR-005 assigned to Ana Gomez"),
    ("trip_completed", "Trip #TR-003 completed ahead of schedule"),
    ("maintenance_due", "DEF-9012 brake inspection needed"),
    ("payment_overdue", "Luzon Logistics payment 15 days overdue"),
    ("insurance_expiry", "GHI-3456 insurance renewal required"),
]
for nt, title in notifications_data:
    Notification.objects.get_or_create(
        user=admin_user, notification_type=nt, title=title,
        defaults={
            "message": f"{title} - please take action.",
            "link": "/dashboard/",
            "is_read": False,
        }
    )
print(f"  10 notifications ready")

print()
print("=" * 50)
print("DATA SEEDING COMPLETE")
print("=" * 50)
print(f"  Users:        {User.objects.count()}")
print(f"  Trucks:       {Truck.objects.count()}")
print(f"  Drivers:      {Driver.objects.count()}")
print(f"  Clients:      {Client.objects.count()}")
print(f"  Trips:        {Trip.objects.count()}")
print(f"  Cargo items:  {Cargo.objects.count()}")
print(f"  Maintenance:  {Maintenance.objects.count()}")
print(f"  Expenses:     {Expense.objects.count()}")
print(f"  Payments:     {Payment.objects.count()}")
print(f"  Notifications:{Notification.objects.count()}")
print()
print("Credentials:")
print("  Admin:      admin / admin123")
print("  Dispatcher: dispatcher1 / password123")
print("  Staff:      staff1 / password123")
