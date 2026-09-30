import json
from pathlib import Path

from lxml import html

from odoo import modules
from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user


@tagged("post_install", "-at_install", "trucalc_branding", "trucalc_pwa_branding")
class TestTruCalcPwaBranding(HttpCase):
    blue = "#022f5b"
    icon_root = "/trucalc_branding/static/src/img"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.internal_login = "pwa-branding@example.com"
        cls.internal_password = "PwaBranding19!"
        new_test_user(
            cls.env,
            cls.internal_login,
            groups="base.group_user",
            context={"no_reset_password": True},
            password=cls.internal_password,
        )

    def test_manifest_identity_preserves_pwa_contract(self):
        self.authenticate(None, None)
        response = self.url_open("/web/manifest.webmanifest")
        self.assertEqual(response.status_code, 200)
        manifest = response.json()
        self.assertEqual(manifest["name"], "TruCalc")
        self.assertEqual(manifest["theme_color"], self.blue)
        self.assertEqual(manifest["background_color"], self.blue)
        self.assertEqual(manifest["scope"], "/odoo")
        self.assertEqual(manifest["start_url"], "/odoo")
        self.assertEqual(manifest["display"], "standalone")
        self.assertIn("shortcuts", manifest)
        self.assertEqual(
            manifest["icons"],
            [
                {
                    "src": f"{self.icon_root}/trucalc-icon-{size}.png",
                    "sizes": size,
                    "type": "image/png",
                }
                for size in ("192x192", "512x512")
            ],
        )
        self.assertNotIn("odoo-icon", json.dumps(manifest).lower())

    def test_scoped_manifest_preserves_scope_and_uses_trucalc_colors(self):
        self.authenticate(None, None)
        response = self.url_open(
            "/web/manifest.scoped_app_manifest"
            "?app_id=trucalc_branding&path=%2Fscoped_app%2Ftrucalc&app_name=TruCalc"
        )
        self.assertEqual(response.status_code, 200)
        manifest = response.json()
        self.assertEqual(manifest["name"], "TruCalc")
        self.assertEqual(manifest["scope"], "/scoped_app/trucalc")
        self.assertEqual(manifest["start_url"], "/scoped_app/trucalc")
        self.assertEqual(manifest["theme_color"], self.blue)
        self.assertEqual(manifest["background_color"], self.blue)

    def test_login_frontend_and_backend_metadata(self):
        self.authenticate(None, None)
        login = self.url_open("/web/login")
        self._assert_browser_metadata(login)

        self.authenticate(self.internal_login, self.internal_password)
        backend = self.url_open("/odoo")
        self._assert_browser_metadata(backend)
        self.assertIn('/web/manifest.webmanifest', backend.text)

    def _assert_browser_metadata(self, response):
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        self.assertEqual(tree.xpath("//meta[@name='theme-color']/@content"), [self.blue])
        self.assertEqual(
            tree.xpath("//link[@rel='apple-touch-icon']/@href"),
            [f"{self.icon_root}/trucalc-icon-ios.png"],
        )
        self.assertEqual(
            tree.xpath("//link[@rel='shortcut icon']/@href"),
            [f"{self.icon_root}/favicon.ico"],
        )
        self.assertNotIn("#71639e", response.text.lower())
        self.assertNotIn("odoo-icon-ios", response.text.lower())

    def test_offline_page_identity_and_retry_contract(self):
        self.authenticate(None, None)
        response = self.url_open("/odoo/offline")
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        self.assertEqual(tree.xpath("string(//title)"), "TruCalc Offline")
        self.assertEqual(tree.xpath("string(//div[contains(@class, 'card')]/h1)"),
                         "TruCalc is temporarily unavailable offline.")
        self.assertEqual(tree.xpath("string(//div[contains(@class, 'card')]/p)"),
                         "Reconnect to the internet and try again.")
        self.assertEqual(tree.xpath("//div[contains(@class, 'card')]/img/@alt"),
                         ["TruCalc logo"])
        self.assertTrue(tree.xpath("//button[@onclick='location.reload()']"))
        self.assertIn("window.addEventListener('online', () => location.reload())", response.text)
        self.assertIn(self.blue, response.text.lower())
        self.assertNotIn("#714b67", response.text.lower())
        self.assertNotIn("odoo logo", response.text.lower())
        self.assertNotIn("odoo will load", response.text.lower())

    def test_service_worker_source_is_unchanged(self):
        self.authenticate(None, None)
        response = self.url_open("/web/service-worker.js")
        source = Path(modules.get_module_path("web"), "static", "src", "service_worker.js")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), source.read_text())
