# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning


class preventive_line(models.Model):
    """Preventive Line"""

    _name = 'public_budget.preventive_line'
    _description = 'Preventive Line'

    name = fields.Char(
        string='Name',
        required=True,
        states={'invoiced': [('readonly', True)], 'closed': [('readonly', True)], 'cancel': [('readonly', True)]}
        )
    account_id = fields.Many2one(
        'account.account',
        string='Account',
        states={'invoiced': [('readonly', True)], 'closed': [('readonly', True)]},
        domain=[('type', 'in', ['other']), ('user_type.report_type', 'in', ['expense','asset'])]
        )
    preventive_amount = fields.Float(
        string='Preventive',
        required=True,
        states={'closed': [('readonly', True)]}
        )
    preventive_status = fields.Selection(
        [(u'draft', u'Draft'), (u'confirmed', u'Confirmed')],
        string='Status',
        readonly=True,
        required=True,
        states={'open': [('readonly', False)], 'confirmed': [('readonly', False)]},
        default='draft'
        )
    available_account_ids = fields.Many2one(
        'account.account',
        string='available_account_ids'
        )
    advance_line = fields.Boolean(
        string='advance_line'
        )
    payment_line_id = fields.Many2one(
        comodel_name='payment.line',
        string='Payment line',
        readonly=True
        )
    remaining_amount = fields.Float(
        string='Remaining Amount',
        compute='_get_amounts'
        )
    definitive_amount = fields.Float(
        string='Definitive Amount',
        compute='_get_amounts'
        )
    invoiced_amount = fields.Float(
        string='Invoiced Amount',
        compute='_get_amounts'
        )
    to_pay_amount = fields.Float(
        string='To Pay Amount',
        compute='_get_amounts'
        )
    paid_amount = fields.Float(
        string='Paid Amount',
        compute='_get_amounts'
        )
    available_account_ids = fields.Many2many(
        comodel_name='account.account',
        string='Available Accounts',
        readonly=True,
        related='budget_position_id.available_account_ids'
        )
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('open', 'Open'), ('confirmed', 'confirmed'), ('definitive', 'definitive'), ('invoiced', 'invoiced'), ('closed', 'closed'), ('cancel', 'Cancel'), ('inactive', 'Inactive')],
        string='States',
        compute='_get_state'
        )
    accounting_state = fields.Selection(
        selection=[('draft', 'Draft'), ('confirmed', 'Confirmed')],
        string='Accounting State',
        store=True,
        compute='_get_accounting_state'
        )
    transaction_id = fields.Many2one(
        'public_budget.transaction',
        ondelete='cascade',
        string='Transaction',
        required=True
        )
    definitive_line_ids = fields.One2many(
        'public_budget.definitive_line',
        'preventive_line_id',
        string='Definitive Lines',
        readonly=True,
        states={'confirmed': [('readonly', False)], 'definitive': [('readonly', False)], 'invoiced': [('readonly', False)]}
        )
    budget_id = fields.Many2one(
        'public_budget.budget',
        string='Budget',
        required=True,
        states={'invoiced': [('readonly', True)], 'closed': [('readonly', True)], 'cancel': [('readonly', True)]},
        domain=[('state', 'not in', ['closed', 'pre_closed'])]
        )
    budget_position_id = fields.Many2one(
        'public_budget.budget_position',
        string='Budget Position',
        required=True,
        states={'invoiced': [('readonly', True)], 'closed': [('readonly', True)], 'cancel': [('readonly', True)]},
        context={'default_type': 'normal'},
        domain=[('type', '=', 'normal')]
        )

    _constraints = [
    ]

    @api.one
    def _get_amounts(self):
        """"""
        raise NotImplementedError

    @api.one
    def _get_state(self):
        """"""
        raise NotImplementedError

    @api.one
    def _get_accounting_state(self):
        """"""
        raise NotImplementedError

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
