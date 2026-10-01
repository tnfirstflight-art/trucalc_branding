from odoo.tests import HttpCase, tagged
from odoo.tools import config


@tagged(
    "post_install",
    "-at_install",
    "trucalc_branding",
    "trucalc_database_route_hardening",
)
class TestDatabaseRouteHardening(HttpCase):
    def test_database_manager_pages_are_denied(self):
        self.assertFalse(config["list_db"])
        for path in ("/web/database/selector", "/web/database/manager"):
            with self.subTest(path=path):
                response = self.url_open(path)
                self.assertEqual(response.status_code, 404)
                self.assertNotIn("Create Database", response.text)
                self.assertNotIn("Restore Database", response.text)

    def test_login_and_health_remain_available(self):
        login = self.url_open("/web/login")
        self.assertEqual(login.status_code, 200)
        self.assertIn("TruCalc", login.text)

        health = self.url_open("/web/health")
        self.assertEqual(health.status_code, 200)
