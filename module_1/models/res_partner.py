# For copyright and license notices, see __manifest__.py file in module root

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _suma(self, a, b):
        return a + b
