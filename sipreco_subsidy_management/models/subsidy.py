from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)


class PublicBudgetSubsidy(models.Model):

    _name = 'public_budget.subsidy'
    _inherits = {
        'public_budget.transaction': 'transaction_id',
    }

    @api.model
    def get_type(self):
        transaction_type = self.env['public_budget.transaction_type'].search(
            [('subsidy', '=', True)], limit=1)
        if not transaction_type:
            raise ValidationError(_(
                'No Se encontró ningún tipo de transacción del tipo subsidio'))
        return transaction_type

    internal_number = fields.Char(
        required=True,
        readonly=True,
    )
    transaction_id = fields.Many2one(
        'public_budget.transaction',
        required=True,
        ondelete='cascade',
        auto_join=True
    )
    # expedient_id = fields.Many2one(
    #     'Expediente Administrativo de Solicitud',
    #     )
    rendiciones_pendientes_otros_subsidios = fields.Monetary(
        'Rend. Pendientes Otros Subsidios',
        help='Rendiciones Pendientes de Otros Subsidios',
        compute='_compute_rendiciones_pendientes_otros_subsidios',
    )
    parliamentary_resolution_date = fields.Date(
        'Fecha de Resolución Parlamentaria',
        required=True,
    )
    parliamentary_expedient = fields.Char(
        'Expediente Parlamentario',
        required=True,
    )
    cargo_date = fields.Date(
        compute='_compute_cargo_data',
        string='Fecha del Cargo',
        store=True,
    )
    dispositional_order = fields.Char(
        'Orden de disposición',
        readonly=True,
    )
    accountability_state = fields.Selection([
        ('pending', 'Cargos Pendientes'),
        ('approved', 'Aprobada'),
    ],
        'Estado',
        # 'Estado de la Rendición',
        compute='_compute_state',
        store=True,
    )
    # accountability_state = fields.Selection([
    #     ('charge_made', 'Cargo Efectuado'),
    #     ('rendition_presented', 'Rendición Presentada'),
    #     ('rendition_approved', 'Rendición Aprobada'),
    # ],
    #     'Estado de la Rendición',
    # )
    accountability_expiry_date = fields.Date(
        compute='_compute_cargo_data',
        string='Vencimiento de Rendición ',
        help='Fecha de vencimiento de presentación de rendición',
        store=True,
    )
    request_expedient_id = fields.Many2one(
        'public_budget.expedient',
        'Expediente de Solicitud',
        required=True,
        # help='Expediente Administrativo de Rendición de Subsidio',
    )
    accountability_administrative_expedient_id = fields.Many2one(
        'public_budget.expedient',
        'Expediente Administrativo de Rendición',
        help='Expediente Administrativo de Rendición de Subsidio',
    )
    other_accountability_expedient_ids = fields.Many2many(
        relation='public_budget_subsidy_other_expedient_rel',
        comodel_name='public_budget.expedient',
        string='Expedientes de Rendicion agregados',
    )
    rendition_ids = fields.One2many(
        'public_budget.subsidy.rendition',
        'subsidy_id',
    )
    note_ids = fields.One2many(
        'public_budget.subsidy.note',
        'subsidy_id',
    )
    destination = fields.Char(
        required=True,
    )
    amount = fields.Monetary(
        required=True,
        # states={'closed': [('readonly', True)]},
    )
    cargo_amount = fields.Monetary(
        'Cargos',
        help='Cargos Efectuados',
        compute='_compute_cargo_data',
        store=True,
    )
    pendientes_rendicion_amount = fields.Monetary(
        'Pendiente Rendición',
        help='Cargos Pendientes de Rendición',
        compute='_compute_cargo_data',
        store=True,
    )
    pendientes_aprobacion_amount = fields.Monetary(
        'Pendiente Aprobación',
        help='Cargos Pendientes de Aprobación',
        compute='_compute_cargo_data',
        store=True,
    )
    rendido_amount = fields.Monetary(
        'Rendido',
        help='Rendiciones Presentadas',
        compute='_compute_amounts',
        store=True,
    )
    aprobado_amount = fields.Monetary(
        'Aprobado',
        help='Rendiciones Aprobadas',
        compute='_compute_amounts',
        store=True,
    )
    revision_amount = fields.Monetary(
        'En Revisión',
        help='Rendiciones presentadas en Revisión',
        compute='_compute_amounts',
        store=True,
    )
    reclaimed = fields.Boolean(string='Reclamado?')

    observations = fields.Text('Observaciones')

    @api.model
    def create(self, vals):
        vals['internal_number'] = self.env[
            'ir.sequence'].next_by_code('subsidy_internal_number') or '/'
        return super(PublicBudgetSubsidy, self.with_context(
            default_type_id=self.get_type().id)).create(vals)

    @api.depends(
        'rendition_ids.rendition_amount',
        'rendition_ids.approved_amount',
    )
    def _compute_amounts(self):
        rendido_amount = sum(
            self.rendition_ids.mapped('rendition_amount'))
        aprobado_amount = sum(
            self.rendition_ids.mapped('approved_amount'))
        self.aprobado_amount = aprobado_amount
        self.rendido_amount = rendido_amount
        self.revision_amount = rendido_amount - aprobado_amount

    @api.onchange('expedient_id', 'partner_id')
    def set_subsidy_name(self):
        self.name = '%s - %s' % (
            self.expedient_id.number or '', self.partner_id.name or '')

    @api.depends(
        'partner_id',
    )
    def _compute_rendiciones_pendientes_otros_subsidios(self):
        if not self.partner_id:
            amount = False
        else:
            others = self.search([
                ('partner_id', '=', self.partner_id.id),
            ])
            others -= self
            amount = sum(others.mapped('pendientes_rendicion_amount'))
        self.rendiciones_pendientes_otros_subsidios = amount

    @api.depends(
        'amount',
        'aprobado_amount',
        'cargo_amount',
    )
    def _compute_state(self):
        # consideramos aprobada solo si hay monto y es igual al cargo y a
        # aprobado
        if (
                self.amount and
                self.amount == self.cargo_amount == self.aprobado_amount):
            accountability_state = 'approved'
        else:
            accountability_state = 'pending'
        self.accountability_state = accountability_state

    @api.depends(
        'rendido_amount',
        'aprobado_amount',
        'payment_group_ids.state',
        'payment_group_ids.payment_date',
        'payment_group_ids.payments_amount',
        # 'payment_group_ids.cargo_date',
        # 'payment_group_ids.cargo_amount',
        # TODO chequear si hace falta esto o no
        'advance_payment_group_ids.state',
        'advance_payment_group_ids.payment_date',
        'advance_payment_group_ids.payments_amount',
        # 'advance_payment_group_ids.cargo_date',
        # 'advance_payment_group_ids.cargo_amount',
    )
    def _compute_cargo_data(self):
        payments = self.payment_group_ids + self.advance_payment_group_ids
        cargo_amount = sum(
            payments.filtered(
                lambda x: x.state == 'posted').mapped('payments_amount'))
        cargo_date = payments.search([
            ('id', 'in', payments.ids),
            ('payment_date', '!=', False),
            # cargo only if payment validated
            ('state', '=', 'posted'),
        ], order='payment_date desc', limit=1).payment_date

        expiry_date = False
        if cargo_date:
            expiry_date = fields.Date.from_string(cargo_date)
            # TODO, parametrizable?
            business_days_to_add = 30
            while business_days_to_add > 0:
                expiry_date = expiry_date + relativedelta(days=+1)
                weekday = expiry_date.weekday()
                # sunday = 6
                if weekday >= 5 or self.env[
                        'hr.holidays.public'].is_public_holiday(expiry_date):
                    continue
                business_days_to_add -= 1
        self.cargo_date = cargo_date
        self.accountability_expiry_date = fields.Date.to_string(
            expiry_date)
        self.cargo_amount = cargo_amount
        self.pendientes_rendicion_amount = (
            cargo_amount - self.rendido_amount)
        self.pendientes_aprobacion_amount = (
            cargo_amount - self.aprobado_amount)

    @api.constrains('cargo_amount', 'rendido_amount')
    def check_renditions(self):
        for rec in self.filtered(lambda x: x.rendido_amount > x.cargo_amount):
            raise ValidationError(_(
                'El importe rendido no puede ser mayor al importe de cargo'))

    @api.onchange('expedient_id')
    def set_expedient_id(self):
        self.parliamentary_expedient = self.\
            expedient_id.parliamentary_expedient

    @api.constrains('amount')
    def check_amount(self):
        for rec in self.filtered(lambda x: not x.amount > 0):
            raise ValidationError(_(
                'El monto debe ser mayor a cero'))

    @api.model
    def _cron_recurring_subsidy_report(self, partner_ids):
        last_week = fields.Date.to_string(
            fields.Date.today() - relativedelta(days=7))
        domain = [('cargo_date', '>=', last_week),
                  ('cargo_date', '<', fields.Date.today())]
        values = {'subsidys': self.search(domain)}
        template = self.env.ref(
            'sipreco_subsidy_management.ir_cron_subsidy_report_week_template')

        template.with_context(
            data=values).send_mail(partner_ids, force_send=True)
