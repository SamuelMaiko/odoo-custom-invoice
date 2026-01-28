from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_datetime = fields.Datetime(
        string="Invoice Datetime",
        default=fields.Datetime.now,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Exact datetime used for metering and billing logic"
    )

    def _compute_old_meter_consumption(self, product):
        self.ensure_one()

        start, end = self._get_metering_period(product)

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

        return reading.value if reading else self.initial_reading
