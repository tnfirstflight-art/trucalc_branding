from markupsafe import Markup
from lxml import html

from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user


@tagged("post_install", "-at_install", "trucalc_branding", "trucalc_portal_branding")
class TestTruCalcPortalBranding(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_login = "portal-branding@example.com"
        cls.portal_password = "PortalBranding19!"
        new_test_user(
            cls.env,
            cls.portal_login,
            groups="base.group_portal",
            context={"no_reset_password": True},
            password=cls.portal_password,
        )

    def _assert_no_odoo_promotion(self, response):
        self.assertNotIn("Powered by Odoo", response.text)
        self.assertNotIn("o_brand_promotion", response.text)
        self.assertNotIn("odoo.com?utm_source=db&amp;utm_medium=portal", response.text)

    def test_generic_portal_home_keeps_layout_without_promotion(self):
        self.authenticate(self.portal_login, self.portal_password)
        response = self.url_open("/my/home", allow_redirects=False)
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        self._assert_no_odoo_promotion(response)
        self.assertTrue(tree.xpath("//div[@id='wrapwrap']"))
        self.assertTrue(tree.xpath("//main//div[@id='wrap']"))
        self.assertTrue(tree.xpath("//footer"))
        self.assertTrue(tree.xpath("//header//a[@href='/my/home']"))
        self.assertTrue(tree.xpath("//header//a[@id='o_logout']"))

    def test_generic_account_keeps_form_without_promotion(self):
        self.authenticate(self.portal_login, self.portal_password)
        response = self.url_open("/my/account", allow_redirects=False)
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        self._assert_no_odoo_promotion(response)
        self.assertTrue(tree.xpath("//form[@name='address_form'][@action='/my/address/submit']"))
        self.assertTrue(tree.xpath("//input[@name='csrf_token']"))

    def test_missing_portal_route_keeps_404_without_promotion(self):
        self.authenticate(self.portal_login, self.portal_password)
        response = self.url_open("/my/trucalc-branding-missing", allow_redirects=False)
        self.assertEqual(response.status_code, 404)
        self._assert_no_odoo_promotion(response)

    def test_brand_promotion_template_renders_empty(self):
        rendered = self.env["ir.qweb"]._render("web.brand_promotion", {})
        self.assertEqual(str(rendered).strip(), "")

    def test_portal_record_sidebar_keeps_functional_content(self):
        rendered = self.env["ir.qweb"]._render(
            "portal.portal_record_sidebar",
            {
                "classes": "o_trucalc_sidebar_test",
                "title": Markup('<h2 id="sidebar-title">Record title</h2>'),
                "entries": Markup(
                    '<a id="sidebar-action" href="/my/action">Record action</a>'
                    '<a id="sidebar-download" href="/my/download">Download</a>'
                ),
            },
        )
        source = str(rendered)
        tree = html.fromstring(source)
        self.assertTrue(tree.xpath("//div[contains(@class, 'o_trucalc_sidebar_test')]"))
        self.assertTrue(tree.xpath("//div[@id='sidebar_content']"))
        self.assertTrue(tree.xpath("//h2[@id='sidebar-title']"))
        self.assertTrue(tree.xpath("//a[@id='sidebar-action'][@href='/my/action']"))
        self.assertTrue(tree.xpath("//a[@id='sidebar-download'][@href='/my/download']"))
        self.assertTrue(tree.xpath("//div[contains(@class, 'vr')]"))
        self.assertNotIn("Powered by", source)
        self.assertNotIn("odoo.com", source.lower())
        self.assertNotIn("Odoo Logo", source)
