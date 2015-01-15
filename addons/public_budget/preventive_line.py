# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning


class preventive_line(models.Model):
    """Preventive Line"""

    _name = 'public_budget.preventive_line'
    _description = 'Preventive Line'

    account_id = fields.Many2one(
        'account.account',
        string='Account',
        states={'invoiced': [('readonly', True)]},
        domain=[('type', 'in', ['other']), ('user_type.report_type', 'in', ['expense','asset'])]
        )
    preventive_amount = fields.Float(
        string='Preventive',
        required=True,
        states={'closed': [('readonly', True)]}
        )
    available_account_ids = fields.Many2one(
        'account.account',
        string='available_account_ids'
        )
    advance_line = fields.Boolean(
        string='advance_line'
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
        selection=[('draft', 'Draft'), ('open', 'Open'), ('definitive', 'definitive'), ('invoiced', 'invoiced'), ('closed', 'closed'), ('cancel', 'Cancel')],
        string='States',
        compute='_get_state'
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
        string='Definitive Lines'
        )
    budget_id = fields.Many2one(
        'public_budget.budget',
        string='Budget',
        required=True,
        states={'invoiced': [('readonly', True)]},
        domain=[('state', 'not in', ['closed', 'pre_closed'])]
        )
    budget_position_id = fields.Many2one(
        'public_budget.budget_position',
        string='Budget Position',
        required=True,
        states={'invoiced': [('readonly', True)]},
        context={'default_type': 'normal'},
        domain=[('type', '=', 'normal')]
        )

    _constraints = [
    ]

    @api.one
    @api.depends(
        'preventive_amount',
        'definitive_line_ids',
    )
    def _get_amounts(self):
        """Update the following fields with the related values to the budget
        and the budget position:
        -definitive_amount: amount sum of definitive lines
        -invoiced_amount: amount sum of lines that are related to an invoice
        line
        -to_pay_amount: amount sum of lines that has a related voucher in draft
        state
        -paid_amount: amount sum of lines that has a related voucher in open
        state
        -balance_amount: diffference between budget position and preventive
        amount
        """

        definitive_amount = False
        invoiced_amount = False
        to_pay_amount = False
        paid_amount = False
        if self.advance_line:
            if self.payment_line_id.order_id.state == 'done':
                definitive_amount = self.preventive_amount
                to_pay_amount = self.preventive_amount
                if self.payment_line_id.voucher_id.state == 'posted':
                    paid_amount = self.preventive_amount
        else:
            definitive_amount = sum([
                definitive.amount
                for definitive in self.definitive_line_ids])
            invoiced_amount = sum([
                definitive.invoiced_amount
                for definitive in self.definitive_line_ids])
            to_pay_amount = sum([
                definitive.to_pay_amount
                for definitive in self.definitive_line_ids])
            paid_amount = sum([
                definitive.paid_amount for definitive in self.definitive_line_ids])

        self.remaining_amount = self.preventive_amount - definitive_amount
        self.definitive_amount = definitive_amount
        self.invoiced_amount = invoiced_amount
        self.to_pay_amount = to_pay_amount
        self.paid_amount = paid_amount

    @api.one
    @api.constrains(
        'budget_id',
        'budget_position_id',
        'preventive_amount')
    def _check_position_balance_amount(self):
        self = self.with_context(budget_id=self.budget_id.id)
        if self.budget_position_id.budget_assignment_allowed and self.budget_position_id.balance_amount < 0.0:
            raise Warning(
                _("There is not Enought Balance Amount on this Budget Position '%s'") %
                (self.budget_position_id.name))

    @api.one
    @api.constrains('definitive_line_ids', 'preventive_amount')
    def _check_number(self):
        if self.preventive_amount < self.definitive_amount:
            raise Warning(
                _("Definitive Amount can't be greater than Preventive Amount"))

    @api.one
    @api.constrains(
        'budget_id',
        'budget_position_id',
        'preventive_amount')
    def _check_position_balance_amount(self):
        self = self.with_context(budget_id=self.budget_id.id)
        if self.budget_position_id.budget_assignment_allowed and self.budget_position_id.balance_amount < 0.0:
            raise Warning(
                _("There is not Enought Balance Amount on this Budget Position '%s'") %
                (self.budget_position_id.name))

    @api.one
    @api.constrains('definitive_line_ids', 'preventive_amount')
    def _check_number(self):
        if self.preventive_amount < self.definitive_amount:
            raise Warning(
                _("Definitive Amount can't be greater than Preventive Amount"))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
