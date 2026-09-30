{
    "name": "TruCalc Branding",
    "version": "19.0.1.1.0",
    "author": "TruCalc",
    "license": "LGPL-3",
    "category": "Hidden",
    "summary": "TruCalc authentication and browser identity",
    "depends": ["web", "portal", "auth_signup"],
    "data": [
        "views/web_templates.xml",
        "views/portal_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "trucalc_branding/static/src/scss/branding.scss",
        ],
        "web.assets_backend": [
            "trucalc_branding/static/src/js/title_service.js",
        ],
        "web.assets_unit_tests": [
            "trucalc_branding/static/tests/title_service.test.js",
        ],
    },
    "installable": True,
    "application": False,
}
