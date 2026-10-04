# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError

CONFIDENTIAL_FIELDS = [
    'system_qty_snapshot',
    'stock_movement_qty',
    'stock_movement_count',
    'expected_qty_at_count',
    'inventory_difference'
]

class FoodwayInventoryCountLine(models.Model):
    _name = 'foodway.inventory.count.line'
    _description = 'Blind Inventory Count Line'
    _order = 'session_id desc, id asc'

    session_id = fields.Many2one(
        'foodway.inventory.count.session',
        string='Session',
        required=True,
        ondelete='cascade',
        index=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='session_id.company_id',
        store=True,
        readonly=True,
        index=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        readonly=True,
        index=True
    )
    barcode = fields.Char(
        string='Barcode',
        related='product_id.barcode',
        store=True,
        readonly=True,
        index=True
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        required=True,
        readonly=True,
        index=True
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        related='product_id.uom_id',
        readonly=True
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot/Serial Number',
        domain="[('product_id', '=', product_id)]"
    )

    is_counted = fields.Boolean(
        string='Is Counted',
        default=False,
        copy=False
    )
    counted_qty = fields.Float(
        string='Physical Counted Qty',
        default=0.0,
        digits='Product Unit of Measure',
        copy=False
    )
    counted_by_user_id = fields.Many2one(
        'res.users',
        string='Counted By',
        readonly=True,
        copy=False
    )
    count_datetime = fields.Datetime(
        string='Last Count Timestamp',
        readonly=True,
        copy=False
    )

    # Confidential Fields — Hidden from Employee via ORM and Server Security Overrides
    system_qty_snapshot = fields.Float(
        string='Snapshot System Qty',
        readonly=True,
        digits='Product Unit of Measure',
        groups='toruq_inventory.group_inventory_count_manager'
    )
    stock_movement_qty = fields.Float(
        string='Stock Movement Net Qty',
        readonly=True,
        digits='Product Unit of Measure',
        groups='toruq_inventory.group_inventory_count_manager'
    )
    stock_movement_count = fields.Integer(
        string='Movements Count',
        readonly=True,
        groups='toruq_inventory.group_inventory_count_manager'
    )
    expected_qty_at_count = fields.Float(
        string='Expected Qty at Count',
        readonly=True,
        digits='Product Unit of Measure',
        groups='toruq_inventory.group_inventory_count_manager'
    )
    inventory_difference = fields.Float(
        string='Discrepancy (Count - Expected)',
        compute='_compute_inventory_difference',
        store=True,
        digits='Product Unit of Measure',
        groups='toruq_inventory.group_inventory_count_manager'
    )

    recount_history = fields.Text(string='Recount Audit Trail', readonly=True)

    @api.depends('is_counted', 'counted_qty', 'expected_qty_at_count')
    def _compute_inventory_difference(self):
        for line in self:
            if line.is_counted:
                line.inventory_difference = line.counted_qty - line.expected_qty_at_count
            else:
                line.inventory_difference = 0.0

    def read(self, fields=None, load='_classic_read'):
        """ Fail-closed server security: Mask theoretical stock fields for non-managers """
        res = super(FoodwayInventoryCountLine, self).read(fields=fields, load=load)
        if not self.env.user.has_group('toruq_inventory.group_inventory_count_manager'):
            for record in res:
                for f in CONFIDENTIAL_FIELDS:
                    if f in record:
                        record[f] = False
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """ Prevent non-managers from aggregating confidential inventory fields """
        if not self.env.user.has_group('toruq_inventory.group_inventory_count_manager'):
            for f in CONFIDENTIAL_FIELDS:
                if any(f in field_str for field_str in fields) or f in (groupby or []):
                    raise AccessError(_("You are not authorized to aggregate confidential inventory quantities."))
        return super(FoodwayInventoryCountLine, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )

    def export_data(self, fields_to_export):
        """ Block non-managers from exporting confidential stock valuation fields """
        if not self.env.user.has_group('toruq_inventory.group_inventory_count_manager'):
            for f in CONFIDENTIAL_FIELDS:
                if f in fields_to_export:
                    raise AccessError(_("You are not authorized to export confidential inventory data."))
        return super(FoodwayInventoryCountLine, self).export_data(fields_to_export)

    def action_update_count(self, input_value, mode='add'):
        self.ensure_one()
        session = self.session_id
        if session.state not in ['opened', 'recount_in_progress']:
            raise UserError(_("Cannot modify counts when session state is '%s'.") % session.state)

        if self.env.user not in session.assigned_user_ids and not self.env.user.has_group('toruq_inventory.group_inventory_count_manager'):
            raise AccessError(_("You are not assigned to count in this session."))

        try:
            val = float(input_value)
        except (ValueError, TypeError):
            raise UserError(_("Invalid quantity input. Please enter a valid number."))

        if val < 0:
            raise UserError(_("Quantity cannot be negative."))

        # Tracked product validation
        if self.product_id.tracking in ['lot', 'serial'] and not self.lot_id and self.env.context.get('require_lot'):
            raise UserError(_("Product '%s' requires a Lot/Serial number.") % self.product_id.display_name)

        if self.product_id.tracking == 'serial' and val > 1.0 and mode == 'add':
            raise UserError(_("Serial tracked product '%s' quantity cannot exceed 1.0 per unit.") % self.product_id.display_name)

        prev_qty = self.counted_qty if self.is_counted else 0.0
        if mode == 'set_total':
            new_qty = val
            op_type = 'set_total'
        else:
            new_qty = prev_qty + val
            op_type = 'add'

        now = fields.Datetime.now()
        self.write({
            'counted_qty': new_qty,
            'is_counted': True,
            'counted_by_user_id': self.env.user.id,
            'count_datetime': now,
        })

        # Log barcode scan entry
        self.env['foodway.inventory.count.entry'].create({
            'session_id': session.id,
            'line_id': self.id,
            'user_id': self.env.user.id,
            'timestamp': now,
            'product_id': self.product_id.id,
            'operation_type': op_type,
            'previous_qty': prev_qty,
            'input_qty': val,
            'new_qty': new_qty,
        })
        return {
            'success': True,
            'line_id': self.id,
            'product': self.product_id.display_name,
            'counted_qty': new_qty,
        }

    def _recompute_movement_comparison(self, eval_datetime=None):
        """ Compatibility wrapper delegating to batch movement calculation """
        return self._batch_recompute_movement_comparison(eval_datetime=eval_datetime)

    def _batch_recompute_movement_comparison(self, eval_datetime=None):
        """ High-performance batch movement engine calculating net stock changes across session lines """
        if not self:
            return

        eval_dt = eval_datetime or fields.Datetime.now()
        sessions = self.mapped('session_id')

        for session in sessions:
            session_lines = self.filtered(lambda l: l.session_id.id == session.id)
            if not session.start_datetime:
                for line in session_lines:
                    line.write({
                        'stock_movement_qty': 0.0,
                        'stock_movement_count': 0,
                        'expected_qty_at_count': line.system_qty_snapshot,
                    })
                continue

            target_loc_ids = self.env['stock.location'].search([('id', 'child_of', session.location_id.id)]).ids
            prod_ids = session_lines.mapped('product_id').ids

            if not prod_ids or not target_loc_ids:
                continue

            # Batch query completed stock moves for all products in scope
            moves = self.env['stock.move'].search([
                ('product_id', 'in', prod_ids),
                ('state', '=', 'done'),
                ('company_id', '=', session.company_id.id),
                ('date', '>=', session.start_datetime),
                ('date', '<=', eval_dt),
                '|',
                ('location_id', 'in', target_loc_ids),
                ('location_dest_id', 'in', target_loc_ids),
            ])

            # Group movement net quantities by product_id
            move_stats = {}
            for m in moves:
                is_dest_in = m.location_dest_id.id in target_loc_ids
                is_src_in = m.location_id.id in target_loc_ids
                p_id = m.product_id.id

                if p_id not in move_stats:
                    move_stats[p_id] = {'net_qty': 0.0, 'count': 0}

                # Incoming boundary move
                if is_dest_in and not is_src_in:
                    move_stats[p_id]['net_qty'] += m.product_uom_qty
                    move_stats[p_id]['count'] += 1
                # Outgoing boundary move
                elif is_src_in and not is_dest_in:
                    move_stats[p_id]['net_qty'] -= m.product_uom_qty
                    move_stats[p_id]['count'] += 1

            # Update lines in batch
            for line in session_lines:
                stats = move_stats.get(line.product_id.id, {'net_qty': 0.0, 'count': 0})
                net_qty = stats['net_qty']
                move_count = stats['count']
                expected = line.system_qty_snapshot + net_qty

                line.write({
                    'stock_movement_qty': net_qty,
                    'stock_movement_count': move_count,
                    'expected_qty_at_count': expected,
                })
