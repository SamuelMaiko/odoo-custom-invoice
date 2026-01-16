from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    previous_reading = fields.Float(
        string='Previous',
        readonly=True
    )

    current_reading = fields.Float(
        string='New'
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
                prev_line = self.env['account.move.line'].search([
                    ('move_id.partner_id', '=', line.move_id.partner_id.id),
                    ('product_id', '=', line.product_id.id),
                    ('move_id.state', '=', 'posted'),
                    ('move_id.date', '<', line.move_id.date),
                ], order='move_id.date desc', limit=1)

                if prev_line:
                    previous = prev_line.current_reading

            line.previous_reading = previous
            line.actual_consumption = line.current_reading - previous
            line.quantity = line.actual_consumption
