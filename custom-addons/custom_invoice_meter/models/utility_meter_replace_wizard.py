# models/utility_meter_replace_wizard.py
from odoo import models, fields, api
from datetime import date


class UtilityMeterReplaceWizard(models.TransientModel):
    _name = 'utility.meter.replace.wizard'
    _description = 'Replace Utility Meter Wizard'

    old_meter_id = fields.Many2one(
        'utility.meter', string='Old Meter', readonly=True
    )
    old_meter_current_reading = fields.Float(
        string='Old Meter Final Reading',
        required=True,
    )
    new_meter_name = fields.Char(
        string='Meter Name', required=True
    )
    product_id = fields.Many2one(
        'product.product', string='Product', readonly=True
    )
    customer_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True
    )
    new_meter_initial_reading = fields.Float(
        string='New Meter Initial Reading', required=True
    )
    replacement_date = fields.Date(
        string='Replacement Date', default=fields.Date.context_today, required=True
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        context = self.env.context
        old_meter = self.env['utility.meter'].browse(context.get('active_id'))
        if old_meter:
            res.update({
                'old_meter_id': old_meter.id,
                'old_meter_current_reading': old_meter.current_reading,
                'product_id': old_meter.product_id.id,
                'customer_id': old_meter.customer_id.id,
            })
        return res

    def action_confirm_replace(self):
        """Replace the meter."""
        self.ensure_one()
        old_meter = self.old_meter_id

        # 1️⃣ Create new meter
        new_meter = self.env['utility.meter'].create({
            'name': self.new_meter_name,
            'product_id': self.product_id.id,
            'customer_id': self.customer_id.id,
            'status': 'active',
            'active_from': self.replacement_date,
            'initial_reading': self.new_meter_initial_reading,
        })

        # 2️⃣ Update old meter
        old_meter.replaced_by_id = new_meter.id
        old_meter.replacement_date = self.replacement_date
        old_meter.status = 'replaced'
        old_meter.final_reading = self.old_meter_current_reading
        old_meter.active_to = self.replacement_date

        return {'type': 'ir.actions.act_window_close'}
