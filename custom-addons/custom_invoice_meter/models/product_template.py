from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_metered_product = fields.Boolean(
        string="Metered Product",
        help="Check if this product uses a meter and requires meter readings on invoices"
    )
