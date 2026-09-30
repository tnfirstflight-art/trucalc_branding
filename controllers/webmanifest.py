import json

from odoo import http
from odoo.addons.web.controllers.webmanifest import WebManifest as WebManifestController


TRUCALC_BLUE = "#022f5b"
TRUCALC_ICON_ROOT = "/trucalc_branding/static/src/img"


class WebManifest(WebManifestController):
    """Keep Odoo's PWA behavior while replacing product identity values."""

    def _get_webmanifest(self):
        manifest = super()._get_webmanifest()
        manifest.update(
            background_color=TRUCALC_BLUE,
            theme_color=TRUCALC_BLUE,
            icons=[
                {
                    "src": f"{TRUCALC_ICON_ROOT}/trucalc-icon-{size}.png",
                    "sizes": size,
                    "type": "image/png",
                }
                for size in ("192x192", "512x512")
            ],
        )
        return manifest

    def _icon_path(self):
        return "trucalc_branding/static/src/img/trucalc-icon-192x192.png"

    @http.route()
    def scoped_app_manifest(self, app_id, path, app_name=""):
        response = super().scoped_app_manifest(app_id, path, app_name)
        manifest = json.loads(response.get_data(as_text=True))
        manifest.update(background_color=TRUCALC_BLUE, theme_color=TRUCALC_BLUE)
        response.set_data(json.dumps(manifest))
        return response
