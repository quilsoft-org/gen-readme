from odoo.tests.common import TransactionCase


class DocumentTestCase(TransactionCase):
    def test_01(self):
        partner_obj = self.env["res.partner"]
        self.assertEqual(partner_obj._suma(4, 2), 6 + 1)
