from lxml import etree

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "trucalc_branding_admin")
class TestBackendAdminBranding(TransactionCase):
    def _combined_arch(self, xmlid):
        return self.env.ref(xmlid)._get_combined_arch()

    def test_marketplace_menus_and_urls_are_retired(self):
        for xmlid in (
            "base.theme_store",
            "base.menu_third_party",
            "base.menu_theme_store",
        ):
            self.assertFalse(self.env.ref(xmlid).active, xmlid)

        for xmlid in (
            "base.action_third_party",
            "base.action_theme_store",
        ):
            action = self.env.ref(xmlid)
            self.assertEqual(action.url, "/odoo/apps")
            self.assertNotIn("odoo.com", action.url.lower())

    def test_module_administration_is_preserved(self):
        apps_menu = self.env.ref("base.menu_apps")
        module_menu = self.env.ref("base.menu_module_tree")
        action = self.env.ref("base.open_module_tree")
        self.assertTrue(apps_menu.active)
        self.assertTrue(module_menu.active)
        self.assertEqual(module_menu.action, action)
        self.assertEqual(action.res_model, "ir.module.module")
        self.assertIn("kanban", action.view_mode)
        self.assertIn("list", action.view_mode)
        self.assertIn("form", action.view_mode)

        module_form = self._combined_arch("base.module_form")
        module_kanban = self._combined_arch("base.module_view_kanban")
        for arch in (module_form, module_kanban):
            self.assertFalse(arch.xpath("//a[contains(@href, 'odoo.com/pricing')]"))

        self.assertTrue(
            module_form.xpath("//button[@name='button_immediate_install']")
        )
        self.assertTrue(
            module_form.xpath("//button[@name='button_immediate_upgrade']")
        )
        self.assertTrue(
            module_kanban.xpath("//button[@name='button_immediate_install']")
        )
        self.assertTrue(
            module_kanban.xpath("//a[@name='button_immediate_upgrade']")
        )
        self.assertTrue(module_form.xpath("//field[@name='installed_version']"))
        self.assertTrue(module_form.xpath("//page[@name='technical_data']"))

    def test_enterprise_promotions_are_absent_from_combined_views(self):
        module_form = self._combined_arch("base.module_form")
        website = module_form.xpath("//field[@name='website']")[0]
        self.assertIn("to_buy", website.get("invisible"))

        module_kanban = self._combined_arch("base.module_view_kanban")
        enterprise_links = module_kanban.xpath(
            "//a[@t-att-href='record.website.raw_value']"
            "[not(contains(@t-if, '!record.to_buy.raw_value'))]"
        )
        self.assertFalse(enterprise_links)

        settings_arch = self._combined_arch(
            "base_setup.res_config_settings_view_form"
        )
        inter_company = settings_arch.xpath("//setting[@id='inter_company']")
        self.assertEqual(len(inter_company), 1)
        self.assertEqual(inter_company[0].get("invisible"), "1")
        self.assertFalse(
            settings_arch.xpath("//widget[@name='iap_buy_more_credits']")
        )
        self.assertFalse(settings_arch.xpath("//setting[@id='iap_credits_setting']"))
        sms_setting = settings_arch.xpath("//setting[@id='sms']")
        self.assertEqual(len(sms_setting), 1)
        self.assertFalse(sms_setting[0].get("documentation"))
        self.assertTrue(settings_arch.xpath("//widget[@name='res_config_edition']"))

    def test_no_security_or_business_records_are_introduced(self):
        module = self.env.ref("base.module_trucalc_branding")
        module_data = self.env["ir.model.data"].search([
            ("module", "=", "trucalc_branding"),
            ("model", "in", ("ir.model.access", "ir.rule", "res.groups")),
        ])
        self.assertFalse(module_data)
        self.assertEqual(module.state, "installed")

    def test_xml_architectures_are_well_formed(self):
        for xmlid in (
            "trucalc_branding.module_form_admin_promotion_cleanup",
            "trucalc_branding.module_kanban_admin_promotion_cleanup",
            "trucalc_branding.settings_admin_promotion_cleanup",
        ):
            etree.fromstring(self.env.ref(xmlid).arch_db.encode())
