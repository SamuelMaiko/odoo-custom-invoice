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
                print("actual consumptioni", line.actual_consumption)
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

        print("YOUR METER", meter)
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
    # @api.depends('product_id', 'move_id.partner_id')
    # def _compute_previous_reading(self):
    #     for line in self:
    #         line.previous_reading = 0.0

    #         # Skip non-metered products
    #         if not line.product_id or not line.product_id.is_metered_product or not line.move_id.partner_id:
    #             continue

    #         prev_line = self.env['account.move.line'].search([
    #             ('partner_id', '=', line.move_id.partner_id.id),
    #             ('product_id', '=', line.product_id.id),
    #             ('move_id.state', '=', 'posted'),
    #             ('current_reading', '!=', False),
    #         ], order='date desc, id desc', limit=1)

    #         if prev_line:
    #             line.previous_reading = prev_line.current_reading

    # @api.depends('previous_reading', 'current_reading', 'product_id')
    # def _compute_actual_consumption(self):
    #     for line in self:
    #         # Only compute for metered products
    #         if not line.product_id or not line.product_id.is_metered_product:
    #             line.actual_consumption = 0.0
    #             continue

    #         if line.current_reading is not None and line.previous_reading is not None:
    #             if line.current_reading != 0 and (line.current_reading < line.previous_reading):
    #                 raise ValidationError(
    #                     "Current reading must be ≥ previous reading.")
    #             line.actual_consumption = line.current_reading - line.previous_reading
    #             line.quantity = line.actual_consumption  # auto-update quantity


# 1. find the invoice period i.e find the last invoice line record for this customer and this product and
# start from created_at datetime to the datetime now, that becomes the invoice period. If there is no invoice line record, the just have the end date and consider all before this date
# 2. Check if there is any meter of this user whose replacement datetime (the current one is date, so I want to duplicate and store a datetime to help with the logic )
# falls within this period. If there are any meters replaced, compute the units used for each of the replaced meters. Which will
# use the final reading on replacement and  subtract the first reading (utility meter reading) after the start date time of the invoice period (which means
# we should also add a new duplicate field to record datetime to the utility meter readings during meter readings logging) or if
# missing just use the initial_reading of the utility meter. That is how the replaced meters calculations will be gotten and gotten as arrays of objects (meter_name, final_reading, previous_reading, comsumed_units)
# I am doing this i.e working with time to ensure that even if meters are replaced in the same day, it can still be reliable and also during doing demos where we won't wait days
# Plus the meters have a status field so that can be used to help the logic, but the duplicate datetime fields need to be added strategically to the models
# 3. Since we have the old meter calculations, now we can calculate the new meter consumption by using the active meter of the user and the user input
# 4. Now to get previous meter reading: Initially the user has no invoice lines, so we fetch the latest reading on the meter i.e the utility meter reading or the initial reading on the meter if the readings are missing, so that becomes our previous reading.
# When the user saves the invoice we will take teh current reading they feed us and add that as a reading to the meter and link that line to the invoice line id so that next time getting the previous reading becomes easy. and this could even help with getting the invoice period
# in future because we could improve the logic to look here first before executing the logic we gave above. Because remember we planned to also add a datetime field here so we could use it.


# for now on the invoice we can just use one column for old meter consumpton called "old meter consumption" which will aggregate the dict key consumption of that array we had talked about (the array is helpful because in future we can just use the extra data to add columns to the view easily instead or recalculating)
