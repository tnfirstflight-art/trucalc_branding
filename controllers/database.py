from odoo import http
from odoo.addons.web.controllers.database import Database
from odoo.tools import config
from werkzeug.exceptions import NotFound


class DatabaseRouteHardening(Database):
    """Hide database-management pages when database listing is disabled."""

    @http.route()
    def selector(self, **kw):
        if not config["list_db"]:
            raise NotFound()
        return super().selector(**kw)

    @http.route()
    def manager(self, **kw):
        if not config["list_db"]:
            raise NotFound()
        return super().manager(**kw)
