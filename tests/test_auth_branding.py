from lxml import html

from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user


@tagged("post_install", "-at_install", "trucalc_branding")
class TestTruCalcBranding(HttpCase):
    favicon_path = "/trucalc_branding/static/src/img/favicon.ico"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_login = "branding-portal@example.com"
        cls.portal_password = "BrandingPortal19!"
        new_test_user(
            cls.env,
            cls.portal_login,
            groups="base.group_portal",
            context={"no_reset_password": True},
            password=cls.portal_password,
        )

    def _assert_identity(self, response):
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        self.assertEqual(tree.xpath("string(//title)"), "TruCalc")
        self.assertEqual(
            tree.xpath("//link[@rel='shortcut icon']/@href"),
            [self.favicon_path],
        )
        self.assertTrue(tree.xpath("//div[contains(@class, 'o_trucalc_auth')]"))
        self.assertNotIn("Powered by Odoo", response.text)
        self.assertNotIn("odoo.com", response.text.lower())
        self.assertNotIn("/web/static/img/favicon.ico", response.text)
        return tree

    def test_login_identity_and_form_contract(self):
        self.authenticate(None, None)
        response = self.url_open("/web/login?redirect=%2Fodoo%3F")
        tree = self._assert_identity(response)
        self.assertTrue(tree.xpath("//form[@action='/web/login'][@method='post']"))
        self.assertTrue(tree.xpath("//input[@name='csrf_token']"))
        self.assertTrue(tree.xpath("//input[@name='redirect'][@value='/odoo?']"))
        self.assertTrue(tree.xpath("//input[@name='type'][@value='password']"))

    def test_signup_identity_and_form_contract(self):
        self.authenticate(None, None)
        response = self.url_open("/web/signup?redirect=%2Fmy")
        tree = self._assert_identity(response)
        self.assertTrue(tree.xpath("//form[contains(@class, 'oe_signup_form')][@method='post']"))
        self.assertTrue(tree.xpath("//input[@name='csrf_token']"))
        self.assertTrue(tree.xpath("//input[@name='redirect'][@value='/my']"))
        self.assertTrue(tree.xpath("//input[@name='token']"))

    def test_reset_identity_and_form_contract(self):
        self.authenticate(None, None)
        response = self.url_open("/web/reset_password?redirect=%2Fmy")
        tree = self._assert_identity(response)
        self.assertTrue(tree.xpath("//form[contains(@class, 'oe_reset_password_form')][@method='post']"))
        self.assertTrue(tree.xpath("//input[@name='csrf_token']"))
        self.assertTrue(tree.xpath("//input[@name='redirect'][@value='/my']"))
        self.assertTrue(tree.xpath("//input[@name='token']"))

    def test_invalid_reset_token_keeps_branded_error_flow(self):
        self.authenticate(None, None)
        response = self.url_open("/web/reset_password?token=not-a-valid-token")
        tree = self._assert_identity(response)
        self.assertTrue(tree.xpath("//p[contains(@class, 'alert-danger')]"))
        self.assertTrue(tree.xpath("//a[@href='/web/login']"))

    def test_login_successful_identity(self):
        self.authenticate(self.portal_login, self.portal_password)
        response = self.url_open("/web/login_successful")
        tree = self._assert_identity(response)
        self.assertIn("You are logged in.", tree.text_content())
        self.assertTrue(tree.xpath("//a[@href='/web/session/logout']"))

    def test_portal_uses_trucalc_favicon(self):
        self.authenticate(self.portal_login, self.portal_password)
        response = self.url_open("/my")
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        self.assertEqual(
            tree.xpath("//link[@rel='shortcut icon']/@href"),
            [self.favicon_path],
        )
        self.assertNotIn("/web/static/img/favicon.ico", response.text)
