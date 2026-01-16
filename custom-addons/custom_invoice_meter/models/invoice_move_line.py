from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    previous_reading = fields.Float(
        string='Previous',
        readonly=True
    )

    current_reading = fields.Float(
        string='New',
        # required=True
    )

    actual_consumption = fields.Float(
        string='Actual',
        compute='_compute_actual_consumption',
        store=True
    )

    @api.depends('current_reading', 'product_id', 'move_id.partner_id')
    def _compute_actual_consumption(self):
        for line in self:
            previous = 0.0
            if line.product_id and line.move_id.partner_id:
                # get previous posted moves for the partner
                prev_move = self.env['account.move'].search([
                    ('partner_id', '=', line.move_id.partner_id.id),
                    ('state', '=', 'posted'),
                    ('date', '<', line.move_id.date)
                ], order='date desc', limit=1)

                if prev_move:
                    prev_line = self.env['account.move.line'].search([
                        ('move_id', '=', prev_move.id),
                        ('product_id', '=', line.product_id.id)
                    ], limit=1)
                    if prev_line:
                        previous = prev_line.current_reading

            line.previous_reading = previous
            line.actual_consumption = line.current_reading - previous
            line.quantity = line.actual_consumption

    @api.constrains('current_reading', 'actual_consumption')
    def _check_consumption(self):
        for line in self:
            if line.actual_consumption < 0:
                raise ValidationError(
                    f"Actual consumption cannot be negative. Check readings for product {line.product_id.name}."
                )
