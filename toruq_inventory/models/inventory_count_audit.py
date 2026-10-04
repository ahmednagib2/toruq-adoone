# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError

class FoodwayInventoryCountAudit(models.Model):
    _name = 'foodway.inventory.count.audit'
    _description = 'Blind Inventory Count Session Audit Log'
    _order = 'timestamp desc, id desc'

    session_id = fields.Many2one('foodway.inventory.count.session', string='Session', required=True, ondelete='cascade', index=True)
    user_id = fields.Many2one('res.users', string='User', required=True)
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now, required=True)
    action = fields.Char(string='Action', required=True)
    message = fields.Text(string='Audit Description')

    def write(self, vals):
        raise UserError(_("Audit log records are immutable historical evidence and cannot be modified."))

    def unlink(self):
        # Only internal ORM cascade deletions during session cleanup are permitted
        for record in self:
            if record.session_id.state not in ['draft', 'cancelled']:
                raise UserError(_("Audit log records are immutable historical evidence and cannot be deleted."))
        return super(FoodwayInventoryCountAudit, self).unlink()
