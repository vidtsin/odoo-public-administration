##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom,
                               location_id, name, origin, values, group_id):
        result = super(ProcurementRule, self)._get_stock_move_values(
            product_id, product_qty, product_uom, location_id, name, origin,
            values, group_id)
        stock_request_id = values.get('stock_request_id', False)
        if stock_request_id:
            stock_request = self.env['stock.request'].browse(stock_request_id)
            stock_request.rule_id = self
            result['name'] = stock_request.description
        return result
