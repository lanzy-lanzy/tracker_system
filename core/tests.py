from decimal import Decimal
import importlib.util
import os
import sys
import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.utils import timezone

from clients.models import Client
from expenses.models import Expense
from notifications.models import Notification
from payments.models import Payment
from tracker_system.middleware import CSPMiddleware
from trips.models import Trip
from trucks.models import Truck


class DeploymentSettingsTests(TestCase):
    def load_settings_with_env(self, **env):
        module_name = f"tracker_system_test_settings_{uuid.uuid4().hex}"
        settings_path = os.path.join(os.path.dirname(__file__), "..", "tracker_system", "settings.py")
        spec = importlib.util.spec_from_file_location(module_name, settings_path)
        module = importlib.util.module_from_spec(spec)

        with patch.dict(os.environ, env, clear=False):
            sys.modules[module_name] = module
            try:
                spec.loader.exec_module(module)
            finally:
                sys.modules.pop(module_name, None)

        return module

    def test_railway_public_domain_is_trusted(self):
        settings_module = self.load_settings_with_env(
            DEBUG="False",
            SECRET_KEY="test-secret",
            RAILWAY_PUBLIC_DOMAIN="tracker-production.up.railway.app",
        )

        self.assertIn("tracker-production.up.railway.app", settings_module.ALLOWED_HOSTS)
        self.assertIn(".up.railway.app", settings_module.ALLOWED_HOSTS)
        self.assertIn(
            "https://tracker-production.up.railway.app",
            settings_module.CSRF_TRUSTED_ORIGINS,
        )

    @override_settings(DEBUG=False)
    def test_production_csp_allows_alpine_expression_evaluation(self):
        response = CSPMiddleware(lambda request: HttpResponse())(None)

        self.assertIn("'unsafe-eval'", response["Content-Security-Policy"])


class ApiContractTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dispatcher", password="password")
        self.user.profile.role = "admin"
        self.user.profile.save(update_fields=["role"])
        self.client.force_login(self.user)

    def test_authenticated_clients_can_list_and_create_trucks(self):
        Truck.objects.create(plate_number="ABC-123", truck_type="flatbed", status="available")

        list_response = self.client.get("/api/trucks/")

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()[0]["plate_number"], "ABC-123")

        create_response = self.client.post(
            "/api/trucks/",
            {
                "plate_number": "XYZ-789",
                "truck_type": "box",
                "status": "maintenance",
                "capacity": "1250.50",
            },
            content_type="application/json",
        )

        self.assertEqual(create_response.status_code, 201)
        self.assertTrue(Truck.objects.filter(plate_number="XYZ-789").exists())

    def test_unauthenticated_api_requests_are_rejected(self):
        self.client.logout()

        response = self.client.get("/api/trucks/")

        self.assertIn(response.status_code, [401, 403])

    def test_trip_status_transition_sets_actual_pickup(self):
        client = Client.objects.create(client_name="Acme", contact_number="555-0100")
        truck = Truck.objects.create(plate_number="TRK-001", truck_type="flatbed")
        trip = Trip.objects.create(
            client=client,
            assigned_truck=truck,
            pickup_location="Warehouse A",
            dropoff_location="Warehouse B",
            scheduled_pickup=timezone.now(),
            scheduled_delivery=timezone.now() + timezone.timedelta(hours=4),
            status="scheduled",
            created_by=self.user,
        )

        response = self.client.patch(
            f"/api/trips/{trip.pk}/status/",
            {"status": "in_transit"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        trip.refresh_from_db()
        self.assertEqual(trip.status, "in_transit")
        self.assertIsNotNone(trip.actual_pickup)

    def test_dashboard_summary_is_available_as_json(self):
        Truck.objects.create(plate_number="TRK-002", truck_type="box", status="available")

        response = self.client.get("/api/dashboard/summary/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total_trucks"], 1)
        self.assertEqual(payload["available_trucks"], 1)
        self.assertIn("monthly_revenue", payload)

    def test_profit_loss_report_is_available_as_json(self):
        today = timezone.now().date()
        client = Client.objects.create(client_name="Acme", contact_number="555-0100")
        trip = Trip.objects.create(
            client=client,
            pickup_location="Warehouse A",
            dropoff_location="Warehouse B",
            scheduled_pickup=timezone.now(),
            scheduled_delivery=timezone.now() + timezone.timedelta(hours=4),
            created_by=self.user,
        )
        Payment.objects.create(
            trip=trip,
            client=client,
            amount_due=Decimal("1500.00"),
            amount_paid=Decimal("1500.00"),
            payment_date=today,
        )
        Expense.objects.create(
            trip=trip,
            expense_type="fuel",
            amount=Decimal("250.00"),
            date=today,
        )

        response = self.client.get(
            f"/api/reports/profit-loss/?start_date={today.isoformat()}&end_date={today.isoformat()}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["revenue"], "1500.00")
        self.assertEqual(response.json()["expenses"], "250.00")
        self.assertEqual(response.json()["profit"], "1250.00")

    def test_notifications_can_be_marked_read_through_api(self):
        Notification.objects.create(
            user=self.user,
            notification_type="trip_updated",
            title="Trip changed",
            message="A trip changed status.",
        )

        response = self.client.post("/api/notifications/mark-all-read/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["unread_count"], 0)
        self.assertFalse(Notification.objects.filter(user=self.user, is_read=False).exists())

    def test_mobile_clients_can_fetch_choice_metadata(self):
        response = self.client.get("/api/meta/choices/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["trips"]["status"][0], {"value": "pending", "label": "Pending"})
        self.assertIn({"value": "available", "label": "Available"}, payload["trucks"]["status"])

    def test_dropdown_invalidation_clears_choice_metadata_cache(self):
        from core.cache_invalidation import invalidate_dropdowns

        cache.set("dropdown:choices", {"stale": True}, 3600)

        invalidate_dropdowns()

        self.assertIsNone(cache.get("dropdown:choices"))

    def test_monthly_trip_report_is_available_as_json(self):
        client = Client.objects.create(client_name="Acme", contact_number="555-0100")
        Trip.objects.create(
            client=client,
            pickup_location="Warehouse A",
            dropoff_location="Warehouse B",
            scheduled_pickup=timezone.now(),
            scheduled_delivery=timezone.now() + timezone.timedelta(hours=4),
            status="delivered",
            created_by=self.user,
        )

        response = self.client.get("/api/reports/monthly-trips/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total_trips"], 1)
        self.assertEqual(payload["completed_trips"], 1)
        self.assertEqual(payload["cancelled_trips"], 0)

    def test_truck_utilization_report_is_available_as_json(self):
        client = Client.objects.create(client_name="Acme", contact_number="555-0100")
        truck = Truck.objects.create(plate_number="TRK-003", truck_type="flatbed", status="available")
        Trip.objects.create(
            client=client,
            assigned_truck=truck,
            pickup_location="Warehouse A",
            dropoff_location="Warehouse B",
            scheduled_pickup=timezone.now(),
            scheduled_delivery=timezone.now() + timezone.timedelta(hours=4),
            status="delivered",
            created_by=self.user,
        )

        response = self.client.get("/api/reports/truck-utilization/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["results"][0]["plate_number"], "TRK-003")
        self.assertEqual(payload["results"][0]["total_trips"], 1)
        self.assertEqual(payload["results"][0]["completed_trips"], 1)

    def test_authenticated_base_pages_load_shared_api_client(self):
        response = self.client.get("/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'src="/static/js/api-client.js"')

    def test_dashboard_template_declares_api_summary_contract(self):
        response = self.client.get("/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-api-dashboard-url="/api/dashboard/summary/"')
        self.assertContains(response, 'data-api-stat="total_trucks"')

    def test_truck_list_template_declares_api_list_contract(self):
        Truck.objects.create(plate_number="ABC-123", truck_type="flatbed", status="available")

        response = self.client.get("/trucks/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-api-list="trucks"')
        self.assertContains(response, 'data-api-url="/api/trucks/"')
        self.assertContains(response, 'src="/static/js/truck-list-api.js"')

    def test_truck_list_renders_first_page_only(self):
        for i in range(55):
            Truck.objects.create(
                plate_number=f"TRK-{i:03d}",
                truck_type="flatbed",
                status="available",
            )

        response = self.client.get("/trucks/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TRK-000")
        self.assertContains(response, "Page 1 of 2")
        self.assertNotContains(response, "TRK-054")

    def test_background_htmx_loads_do_not_use_global_spinner(self):
        response = self.client.get("/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "shouldShowGlobalSpinner")
        self.assertContains(response, 'hx-trigger="load"')

    def test_sidebar_navigation_uses_htmx_boosted_app_shell_swaps(self):
        response = self.client.get("/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="app-shell"')
        self.assertContains(response, 'hx-boost="true"')
        self.assertContains(response, 'hx-target="#app-shell"')
        self.assertContains(response, 'hx-select="#app-shell"')
        self.assertContains(response, "requestConfig.boosted")
        self.assertContains(response, "target.id === 'app-shell'")

    def test_page_scripts_can_run_after_boosted_swaps(self):
        with open("static/js/dashboard-api.js", encoding="utf-8") as f:
            dashboard_js = f.read()
        with open("static/js/truck-list-api.js", encoding="utf-8") as f:
            truck_js = f.read()

        self.assertIn("document.readyState", dashboard_js)
        self.assertIn("document.readyState", truck_js)
