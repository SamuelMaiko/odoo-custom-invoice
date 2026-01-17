from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    previous_reading = fields.Float(
        string="Previous",
        compute='_compute_previous_reading',
        store=True,
    )

    current_reading = fields.Float(
        string='New',
        required=True
    )

    actual_consumption = fields.Float(
        string='Actual',
        compute='_compute_actual_consumption',
        store=True,
    )

    @api.depends('product_id', 'move_id.partner_id')
    def _compute_previous_reading(self):
        for line in self:
            line.previous_reading = 0.0

            if not line.product_id or not line.move_id.partner_id:
                continue

            prev_line = self.env['account.move.line'].search([
                ('partner_id', '=', line.move_id.partner_id.id),  # direct field
                ('product_id', '=', line.product_id.id),
                ('move_id.state', '=', 'posted'),
                ('current_reading', '!=', False),
            ], order='date desc, id desc', limit=1)

            if prev_line:
                line.previous_reading = prev_line.current_reading

    @api.depends('previous_reading', 'current_reading')
    def _compute_actual_consumption(self):
        for line in self:
            if line.current_reading is not None and line.previous_reading is not None:
                if line.current_reading != 0 and (line.current_reading < line.previous_reading):
                    raise ValidationError(
                        "Current reading must be ≥ previous reading.")
                line.actual_consumption = line.current_reading - line.previous_reading
                line.quantity = line.actual_consumption  # auto-update quantity
