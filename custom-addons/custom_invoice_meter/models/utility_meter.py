# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class UtilityMeter(models.Model):
    _name = 'utility.meter'
    _description = 'Utility Meter'
    _order = 'name, active_from desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Serial Number / Name',
        required=True,
        copy=False,
        index=True,
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        index=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain=[('is_metered_product', '=', True)],
    )

    status = fields.Selection([
        ('active', 'Active'),
        ('replaced', 'Replaced'),
    ], string='Status', default='active', required=True, index=True)

    active_from = fields.Date(
        string='Active From',
        required=True,
    )
    active_to = fields.Date(
        string='Active To',
    )
    active_from_datetime = fields.Datetime(
        string='Active From (Datetime)',
        required=True,
        default=lambda self: fields.Datetime.now(),  # fallback to current timestamp
    )

    active_to_datetime = fields.Datetime(
        string='Active To (Datetime)',
    )

    initial_reading = fields.Float(
        string='Initial Reading',
        digits=(16, 3),
        default=0.0,
    )
    final_reading = fields.Float(
        string='Final Reading (when replaced)',
        digits=(16, 3),
        default=0.0,
        readonly=True,
        states={'replaced': [('readonly', False)]},
    )

    replaced_by_id = fields.Many2one(
        'utility.meter',
        string='Replaced By',
        index=True,
        ondelete='set null',
    )
    replacement_date = fields.Date(
        string='Replacement Date',
    )

    replacement_datetime = fields.Datetime(
        string="Replacement Datetime",
        readonly=True,
        help="Exact datetime when the meter was replaced"
    )

    # Computed / relational fields
    current_reading = fields.Float(
        string='Latest Reading',
        compute='_compute_current_reading',
        store=False,
    )

    reading_ids = fields.One2many(
        'utility.meter.reading',
        'meter_id',
        string='Readings',
    )

    @api.constrains('status', 'replacement_date')
    def _check_replacement_date(self):
        for meter in self:
            if meter.status == 'replaced' and not meter.replacement_date:
                raise ValidationError(
                    "Replacement date is required when a meter is replaced."
                )

    @api.constrains('status', 'replaced_by_id')
    def _check_replaced_by(self):
        for meter in self:
            if meter.status == 'replaced' and not meter.replaced_by_id:
                raise ValidationError(
                    "You must specify the new meter when replacing a meter."
                )

    # @api.constrains('customer_id', 'product_id', 'status')
    # def _check_single_active_meter(self):
    #     for meter in self:
    #         if meter.status == 'active':
    #             domain = [
    #                 ('customer_id', '=', meter.customer_id.id),
    #                 ('product_id', '=', meter.product_id.id),
    #                 ('status', '=', 'active'),
    #                 ('id', '!=', meter.id),
    #             ]
    #             if self.search_count(domain):
    #                 raise ValidationError(
    #                     "Only one active meter is allowed per customer and product."
    #                 )

    @api.depends('reading_ids.reading_value', 'reading_ids.reading_date')
    def _compute_current_reading(self):
        for meter in self:
            if not meter.reading_ids:
                meter.current_reading = meter.initial_reading
                continue
            latest = meter.reading_ids.sorted('reading_date', reverse=True)[:1]
            meter.current_reading = latest.reading_value if latest else meter.initial_reading

    @api.constrains('product_id')
    def _check_metered_product(self):
        for meter in self:
            if meter.product_id and not meter.product_id.is_metered_product:
                raise ValidationError(
                    "Selected product is not marked as a metered product."
                )

    def action_replace_meter(self):
        return {
            'name': 'Replace Meter',
            'type': 'ir.actions.act_window',
            'res_model': 'utility.meter.replace.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('custom_invoice_meter.view_utility_meter_replace_wizard_form').id,
            'target': 'new',
            'context': {'active_id': self.id},
        }

    # @api.onchange('status')
    # def _onchange_status(self):
    #     if self.status == 'replaced':
    #         if not self.replacement_date:
    #             self.replacement_date = fields.Date.today()
    #     else:
    #         self.replacement_date = False
    #         self.final_reading = 0.0
    #         self.replaced_by_id = False

    # _sql_constraints = [
    #     ('name_unique', 'UNIQUE(name)',
    #      'Meter serial number must be unique!'),
    # ]

    def _compute_consumption(self, start, end):
        self.ensure_one()

        start_reading = self._get_previous_reading(start)

        end_reading = self.env['utility.meter.reading'].search([
            ('meter_id', '=', self.id),
            ('reading_datetime', '<=', end),
        ], order='reading_datetime desc', limit=1)

        final_value = (
            end_reading.value
            if end_reading else self.current_reading
        )

        return {
            'meter_id': self.id,
            'meter_name': self.name,
            'previous_reading': start_reading,
            'final_reading': final_value,
            'consumed_units': final_value - start_reading,
        }

    def _get_previous_reading(self, start_datetime):
        self.ensure_one()

        reading = self.env['utility.meter.reading'].search([
            ('meter_id', '=', self.id),
            ('reading_datetime', '<=', start_datetime),
        ], order='reading_datetime desc', limit=1)

        return reading.value if reading else self.initial_reading
