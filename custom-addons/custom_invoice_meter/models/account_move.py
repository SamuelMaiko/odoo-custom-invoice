from odoo import fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_datetime = fields.Datetime(
        string="Invoice Datetime",
        default=fields.Datetime.now,
        readonly=True,
        # states={'draft': [('readonly', False)]},
        store=True,
        help="Exact datetime used for metering and billing logic"
    )

    def action_post(self):
        res = super().action_post()
        # after posting, write meter readings for all lines
        for move in self:
            for line in move.line_ids:
                if hasattr(line, 'write_meter_reading'):
                    line.write_meter_reading()
        return res

    def _compute_old_meter_consumption(self, product):
        self.ensure_one()

        start, end = self._get_metering_period(product)
        print("START OF PERIOD", start)
        print("END OF PERIOD", end)

        meters = self.env['utility.meter']._get_replaced_meters_in_period(
            self.partner_id,
            product,
            start,
            end,
        )

        results = []
        total = 0

        for meter in meters:
            data = meter._compute_consumption(
                start, meter.replacement_datetime)
            results.append(data)
            total += data['consumed_units']

        return {
            'total': total,
            'breakdown': results,
        }

    def _get_previous_reading(self, start_datetime):
        self.ensure_one()

        reading = self.env['utility.meter.reading'].search([
            ('meter_id', '=', self.id),
            ('reading_datetime', '<=', start_datetime),
        ], order='reading_datetime desc', limit=1)

        return reading.reading_value if reading else self.initial_reading

    def _get_last_invoice_datetime(self, partner, product):
        """Return the last posted invoice datetime for this customer and product."""
        self.ensure_one()

        lines = self.env['account.move.line'].search([
            ('move_id.partner_id', '=', partner.id),
            ('product_id', '=', product.id),
            ('move_id.state', '=', 'posted'),
            ('move_id.move_type', 'in', ['out_invoice', 'out_refund']),
        ])

        if not lines:
            return None

        # Sort in Python by invoice_datetime
        last_line = max(lines, key=lambda l: l.move_id.invoice_datetime)
        return last_line.move_id.invoice_datetime

    # _get_metering_period
    def _get_metering_period(self, product):
        """
        Returns (start_datetime, end_datetime)
        """
        self.ensure_one()
        end = self.invoice_datetime

        lines = self.env['account.move.line'].search([
            ('move_id.state', '=', 'posted'),
            ('move_id.move_type', '=', 'out_invoice'),
            ('move_id.partner_id', '=', self.partner_id.id),
            ('product_id', '=', product.id),
            ('id', '!=', self.id),
        ])

        last_line = max(
            lines, key=lambda l: l.move_id.invoice_datetime) if lines else None
        start = last_line.move_id.invoice_datetime if last_line else False

        return start, end

    def action_replace_meter(self):
        self.ensure_one()

        if self.state != 'draft':
            raise ValidationError(
                "Meter replacement is only allowed in draft invoices."
            )

        meter_lines = self.invoice_line_ids.filtered(
            lambda l: l.product_id.is_metered_product
        )

        if not meter_lines:
            raise ValidationError("No metered invoice line found.")

        if len(meter_lines) > 1:
            raise ValidationError(
                "Multiple metered lines found. Cannot determine target meter."
            )

        line = meter_lines[0]
        partner = self.partner_id
        product = line.product_id

        active_meter = self.env['utility.meter'].search([
            ('customer_id', '=', partner.id),
            ('product_id', '=', product.id),
            ('status', '=', 'active'),
        ], limit=1)

        print("active_meter", active_meter)

        if not active_meter:
            raise ValidationError(
                "No active meter found for this customer and product."
            )

        return {
            "type": "ir.actions.act_window",
            "name": "Replace Meter",
            "res_model": "utility.meter.replace.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_meter_id": active_meter.id,
                "default_invoice_id": self.id,
                "default_invoice_line_id": line.id,
                "default_effective_datetime": self.invoice_datetime,
            },
        }
