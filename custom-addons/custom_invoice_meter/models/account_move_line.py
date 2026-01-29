from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    previous_reading = fields.Float(
        string="Previous",
        compute='_compute_readings',
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
    old_meter_consumption = fields.Float(
        string="Old Meter(s)",
        compute='_compute_readings',
        store=True,
    )

    @api.depends('product_id', 'move_id.partner_id', 'move_id.invoice_datetime')
    def _compute_readings(self):
        for line in self:
            partner = line.move_id.partner_id
            product = line.product_id
            invoice_dt = line.move_id.invoice_datetime

            if not partner or not product or not invoice_dt:
                line.previous_reading = 0
                line.actual_consumption = 0
                line.old_meter_consumption = 0
                continue

            # 1️⃣ Compute old meter consumption
            old_meter_data = line.move_id._compute_old_meter_consumption(
                product)
            print("HERE", old_meter_data)
            line.old_meter_consumption = old_meter_data['total']

            # 2️⃣ Get the active meter
            active_meter = self.env['utility.meter'].search([
                ('customer_id', '=', partner.id),
                ('product_id', '=', product.id),
                ('status', '=', 'active')
            ], limit=1)

            if not active_meter:
                line.previous_reading = 0
                line.actual_consumption = 0
                continue

            # 3️⃣ Compute previous reading
            start_datetime = (line.move_id._get_last_invoice_datetime(partner, product)
                              or invoice_dt)
            line.previous_reading = active_meter._get_previous_reading(
                start_datetime)

            # 4️⃣ Compute actual consumption
            if line.current_reading:
                line.actual_consumption = line.current_reading - line.previous_reading
                line.quantity = line.actual_consumption+line.old_meter_consumption
            else:
                line.actual_consumption = 0

    @api.onchange('product_id', 'move_id.partner_id')
    def _set_previous_reading(self):
        """Set previous reading from the latest meter reading."""
        for line in self:
            if not line.product_id or not line.move_id.partner_id:
                continue
            meter = self.env['utility.meter'].search([
                ('customer_id', '=', line.move_id.partner_id.id),
                ('product_id', '=', line.product_id.id),
                ('status', '=', 'active'),
            ], limit=1, order='active_from_datetime desc')
            if meter:
                start_dt = line.move_id._get_last_invoice_datetime(line.move_id.partner_id, line.product_id) \
                    or meter.active_from_datetime
                print("START DATE", start_dt)
                print("PREVIOUS READING", meter._get_previous_reading(start_dt))
                line.previous_reading = meter._get_previous_reading(start_dt)

    @api.depends('current_reading', 'previous_reading', 'old_meter_consumption')
    def _compute_actual_consumption(self):
        for line in self:
            if line.current_reading and line.previous_reading is not None:
                line.actual_consumption = line.current_reading - \
                    line.previous_reading
                line.quantity = line.actual_consumption+line.old_meter_consumption

    def write_meter_reading(self):
        """Write the current reading to the linked utility meter."""
        self.ensure_one()
        # meter = getattr(self, 'meter_id', False)
        meter = self.env['utility.meter'].search([
            ('customer_id', '=', self.move_id.partner_id.id),
            ('product_id', '=', self.product_id.id),
            ('status', '=', 'active'),
        ], limit=1)

        if not meter:
            return

        # Determine previous reading if not already set
        if not self.previous_reading:
            start_dt = self.move_id.invoice_datetime
            self.previous_reading = meter._get_previous_reading(start_dt)

        # Compute actual consumption
        self.actual_consumption = self.current_reading - self.previous_reading

        # Record reading on the meter
        self.env['utility.meter.reading'].create({
            'meter_id': meter.id,
            'reading_date': fields.Date.today(),
            'reading_datetime': self.move_id.invoice_datetime,
            'reading_value': self.current_reading,
            'invoice_line_id': self.id,
            'reading_type': 'periodic',
        })
