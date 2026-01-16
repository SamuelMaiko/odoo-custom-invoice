from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    previous_reading = fields.Float(
        string='Previous',
        readonly=True,
        copy=False,
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

    @api.depends('previous_reading', 'current_reading')
    def _compute_actual_consumption(self):
        for rec in self:
            if rec.current_reading and rec.previous_reading and rec.current_reading < rec.previous_reading:
                raise ValidationError(
                    "Current reading must be ≥ previous reading.")
            rec.actual_consumption = (
                rec.current_reading or 0.0) - (rec.previous_reading or 0.0)

    @api.onchange('product_id')
    def _onchange_product_id_custom(self):
        if not self.product_id or not self.move_id.partner_id:
            self.previous_reading = 0.0
            return

        # Safe: use many2one value directly (works with NewId)
        domain = [
            ('partner_id', '=', self.move_id.partner_id.id),           # ← key fix
            ('product_id', '=', self.product_id.id),
            ('move_id.state', '=', 'posted'),
            # include refunds if needed
            ('move_id.move_type', 'in', ('out_invoice', 'out_refund')),
            # optional: only lines that had a reading
            ('current_reading', '!=', False),
        ]

        last_line = self.env['account.move.line'].search(
            domain, order='date desc, move_id desc, id desc', limit=1)

        if last_line:
            self.previous_reading = last_line.current_reading
        else:
            self.previous_reading = 0.0   # or False / keep empty — your choice

        # Trigger consumption & quantity update
        self._onchange_current_reading_custom()

    @api.onchange('current_reading')
    def _onchange_current_reading_custom(self):
        if self.current_reading or self.previous_reading:  # allow 0
            self._compute_actual_consumption()   # manual call since it's @api.depends
            self.quantity = self.actual_consumption   # auto-set delivered/consumed qty

    # Optional: make current_reading required only on posted invoices
    # (uncomment in xml view instead of field definition)
    # current_reading = fields.Float(..., required=False)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('partner_id')
    def _onchange_partner_id_custom(self):
        """ Re-compute previous readings on all lines when customer changes late """
        if self.partner_id:
            for line in self.invoice_line_ids:
                if line.product_id:
                    line._onchange_product_id_custom()
        else:
            for line in self.invoice_line_ids:
                line.previous_reading = 0.0
