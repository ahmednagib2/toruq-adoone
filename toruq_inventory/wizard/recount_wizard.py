# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError

class FoodwayInventoryCountRecountWizard(models.TransientModel):
    _name = 'foodway.inventory.count.recount.wizard'
    _description = 'Blind Inventory Count Recount Wizard'

    session_id = fields.Many2one('foodway.inventory.count.session', string='Session', required=True)
    recount_scope = fields.Selection([
        ('discrepancy_only', 'Discrepancies Only / الفروقات فقط'),
        ('all', 'All Session Lines / جميع السطور'),
        ('selected', 'Selected Lines / سطور محدودة')
    ], string='Recount Scope', default='discrepancy_only', required=True)

    line_ids = fields.Many2many(
        'foodway.inventory.count.line',
        'foodway_recount_line_rel',
        'wizard_id',
        'line_id',
        string='Lines to Recount',
        domain="[('session_id', '=', session_id)]"
    )
    reason = fields.Text(string='Recount Reason & Instructions', required=True)

    def action_process_recount(self):
        self.ensure_one()
        if not self.env.user.has_group('toruq_inventory.group_inventory_count_manager'):
            raise AccessError(_("Only Inventory Managers can request a recount."))

        if self.recount_scope == 'discrepancy_only':
            target_lines = self.session_id.line_ids.filtered(lambda l: l.is_counted and l.inventory_difference != 0.0)
        elif self.recount_scope == 'all':
            target_lines = self.session_id.line_ids
        else:
            target_lines = self.line_ids

        if not target_lines:
            raise UserError(_("No lines match the selected recount scope."))

        self.session_id.action_request_recount(reason=self.reason, line_ids=target_lines)
        return {'type': 'ir.actions.act_window_close'}
