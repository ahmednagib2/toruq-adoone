# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError

class FoodwayInventoryCountEntry(models.Model):
    _name = 'foodway.inventory.count.entry'
    _description = 'Blind Inventory Count Scan Entry Audit'
    _order = 'timestamp desc, id desc'

    session_id = fields.Many2one('foodway.inventory.count.session', string='Session', required=True, ondelete='cascade', index=True)
    line_id = fields.Many2one('foodway.inventory.count.line', string='Count Line', ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Counter User', required=True)
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now, required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)

    operation_type = fields.Selection([
        ('add', 'Add Quantity'),
        ('set_total', 'Set Total Quantity')
    ], string='Operation Mode', required=True)

    previous_qty = fields.Float(string='Previous Qty', readonly=True)
    input_qty = fields.Float(string='Scanned Input Qty', readonly=True)
    new_qty = fields.Float(string='Resulting Qty', readonly=True)

    def write(self, vals):
        raise UserError(_("Scan entry audit logs are immutable historical evidence and cannot be modified."))

    def unlink(self):
        # Only internal ORM cascade deletions during session cleanup are permitted
        for record in self:
            if record.session_id.state not in ['draft', 'cancelled']:
                raise UserError(_("Scan entry audit logs are immutable historical evidence and cannot be deleted."))
        return super(FoodwayInventoryCountEntry, self).unlink()
