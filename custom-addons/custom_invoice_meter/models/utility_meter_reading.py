
from odoo import models, fields, api


class UtilityMeterReading(models.Model):
    _name = 'utility.meter.reading'
    _description = 'Meter Reading'
    _order = 'reading_date desc, id desc'
    _rec_name = 'reading_date'

    meter_id = fields.Many2one(
        'utility.meter',
        string='Meter',
        required=True,
        ondelete='cascade',
        index=True,
    )

    reading_date = fields.Date(
        string='Reading Date',
        required=True,
        index=True,
    )

    reading_value = fields.Float(
        string='Reading Value',
        digits=(16, 3),
        required=True,
    )

    reading_type = fields.Selection([
        ('initial', 'Initial'),
        ('final', 'Final'),
        ('periodic', 'Period'),
    ], string='Reading Type', default='periodic', required=True)

    # Optional useful fields
    # employee_id = fields.Many2one('hr.employee', string='Read by')
    notes = fields.Text(string='Notes')

    reading_datetime = fields.Datetime(
        string='Reading Datetime',
        required=True,
        default=lambda self: fields.Datetime.now(),  # fallback to current timestamp
        help="Exact datetime the reading was taken"
    )

    invoice_line_id = fields.Many2one(
        'account.move.line',
        string="Invoice Line",
        ondelete='set null',
        help="Invoice line that generated this reading"
    )

    _sql_constraints = [
        ('meter_date_unique', 'UNIQUE(meter_id, reading_date)',
         'Only one reading per meter per date is allowed'),
    ]

    # @api.model
    # def create(self, vals):
    #     record = super().create(vals)
    #     # Optional: update final_reading on old meter when a final reading is recorded
    #     if record.reading_type == 'final' and record.meter_id.status == 'active':
    #         record.meter_id.write({
    #             'status': 'replaced',
    #             'final_reading': record.reading_value,
    #             'active_to': record.reading_date,
    #         })
    #     return record
