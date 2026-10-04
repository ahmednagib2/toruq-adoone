# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError

class FoodwayInventoryCountSession(models.Model):
    _name = 'foodway.inventory.count.session'
    _description = 'Blind Inventory Count Session'
    _order = 'id desc'

    name = fields.Char(
        string='Session Reference',
        required=True,
        readonly=True,
        default=lambda self: _('New'),
        copy=False
    )
    session_name = fields.Char(
        string='Session Title',
        required=True,
        default=lambda self: _('Physical Count %s') % fields.Date.today()
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('opened', 'In Progress'),
        ('submitted', 'Submitted'),
        ('recount_requested', 'Recount Requested'),
        ('recount_in_progress', 'Recount In Progress'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True, copy=False)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
        domain="[('company_id', '=', company_id)]"
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Count Location',
        required=True,
        domain="[('usage', '=', 'internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
    include_child_locations = fields.Boolean(
        string='Include Child Locations',
        default=True,
        help="If checked, includes stock quants in sub-locations of the selected location."
    )

    product_scope = fields.Selection([
        ('all', 'All Storable Products'),
        ('category', 'By Category'),
        ('products', 'Specific Products')
    ], string='Product Scope', default='all', required=True)

    category_ids = fields.Many2many(
        'product.category',
        'foodway_session_categ_rel',
        'session_id', 'category_id',
        string='Product Categories'
    )
    product_ids = fields.Many2many(
        'product.product',
        'foodway_session_product_rel',
        'session_id', 'product_id',
        string='Specific Products',
        domain="[('is_storable', '=', True)]"
    )

    assigned_user_ids = fields.Many2many(
        'res.users',
        'foodway_session_user_rel',
        'session_id', 'user_id',
        string='Assigned Employees',
        required=True,
        help="Employees authorized to scan/count products in this session."
    )

    line_ids = fields.One2many(
        'foodway.inventory.count.line',
        'session_id',
        string='Count Lines'
    )
    entry_ids = fields.One2many(
        'foodway.inventory.count.entry',
        'session_id',
        string='Barcode Scan Entries'
    )
    audit_log_ids = fields.One2many(
        'foodway.inventory.count.audit',
        'session_id',
        string='Audit Logs'
    )

    # Honeywell Wedge Quick Scan Fields
    scan_barcode = fields.Char(string='Scan Barcode / مسح الباركود', copy=False)
    scan_qty = fields.Float(string='Scan Quantity / الكمية', default=1.0)
    scan_mode = fields.Selection([
        ('add', 'إضافة (+1 أو الكمية)'),
        ('set_total', 'تحديد الإجمالي (Set Total)')
    ], string='Scan Mode', default='add', required=True)

    # Last Scan Feedback Fields
    last_scanned_product_id = fields.Many2one('product.product', string='آخر منتج تم مسحه', readonly=True)
    last_scanned_barcode = fields.Char(string='آخر باركود', readonly=True)
    last_scanned_previous_qty = fields.Float(string='الكمية السابقة', readonly=True)
    last_scanned_added_qty = fields.Float(string='الكمية المضافة الآن', readonly=True)
    last_scanned_new_qty = fields.Float(string='الإجمالي الحقيقي حالياً', readonly=True)
    last_scanned_time = fields.Datetime(string='وقت آخر مسح', readonly=True)

    start_datetime = fields.Datetime(string='Start Timestamp', readonly=True)
    opened_by_user_id = fields.Many2one('res.users', string='Opened By', readonly=True)
    submitted_datetime = fields.Datetime(string='Submitted Timestamp', readonly=True)
    submitted_by_user_id = fields.Many2one('res.users', string='Submitted By', readonly=True)
    approved_datetime = fields.Datetime(string='Approved Timestamp', readonly=True)
    approved_by_user_id = fields.Many2one('res.users', string='Approved By', readonly=True)

    recount_round = fields.Integer(string='Recount Round', default=0, readonly=True)
    adjustment_applied = fields.Boolean(string='Adjustment Applied', default=False, readonly=True)
    adjustment_move_ids = fields.Many2many(
        'stock.move',
        'foodway_session_move_rel',
        'session_id', 'move_id',
        string='Stock Adjustment Moves',
        readonly=True
    )
    reliability_warning = fields.Text(string='Reliability Warning', readonly=True)

    total_lines_count = fields.Integer(string='Total Products', compute='_compute_line_metrics', store=True)
    counted_lines_count = fields.Integer(string='Counted Products', compute='_compute_line_metrics', store=True)
    uncounted_lines_count = fields.Integer(string='Uncounted Products', compute='_compute_line_metrics', store=True)
    discrepancy_lines_count = fields.Integer(
        string='Discrepancy Count',
        compute='_compute_line_metrics',
        store=True,
        groups='toruq_inventory.group_inventory_count_manager'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('foodway.inventory.count.session') or _('New')
        sessions = super(FoodwayInventoryCountSession, self).create(vals_list)
        for session in sessions:
            session._create_audit_log('create', _('Inventory count session created.'))
        return sessions

    @api.depends('line_ids.is_counted', 'line_ids.inventory_difference')
    def _compute_line_metrics(self):
        for session in self:
            session.total_lines_count = len(session.line_ids)
            session.counted_lines_count = len(session.line_ids.filtered(lambda l: l.is_counted))
            session.uncounted_lines_count = session.total_lines_count - session.counted_lines_count
            if self.env.user.has_group('toruq_inventory.group_inventory_count_manager'):
                session.discrepancy_lines_count = len(session.line_ids.filtered(lambda l: l.is_counted and l.inventory_difference != 0))
            else:
                session.discrepancy_lines_count = 0

    def action_scan_barcode(self):
        self.ensure_one()
        if self.state not in ['opened', 'recount_in_progress']:
            raise UserError(_("Cannot scan barcodes when session state is '%s'.") % self.state)

        if not self.scan_barcode:
            return True

        barcode_str = self.scan_barcode.strip()
        lines = self.line_ids.filtered(lambda l: (l.barcode and l.barcode.strip() == barcode_str) or (l.product_id.default_code and l.product_id.default_code.strip() == barcode_str))
        
        if not lines:
            product = self.env['product.product'].search([
                '|', ('barcode', '=', barcode_str), ('default_code', '=', barcode_str)
            ], limit=1)
            if product:
                lines = self.line_ids.filtered(lambda l: l.product_id.id == product.id)

        if not lines:
            raise UserError(_("الباركود '%s' غير موجود ضمن قائمة منتجات هذه الجلسة!") % barcode_str)

        target_line = lines[0]
        prev_qty = target_line.counted_qty if target_line.is_counted else 0.0
        mode = self.scan_mode or 'add'
        qty = self.scan_qty if self.scan_qty > 0 else 1.0

        target_line.action_update_count(qty, mode=mode)
        new_total = target_line.counted_qty

        added_val = qty if mode == 'add' else (new_total - prev_qty)

        self.write({
            'scan_barcode': False,
            'scan_qty': 1.0,
            'last_scanned_product_id': target_line.product_id.id,
            'last_scanned_barcode': barcode_str,
            'last_scanned_previous_qty': prev_qty,
            'last_scanned_added_qty': added_val,
            'last_scanned_new_qty': new_total,
            'last_scanned_time': fields.Datetime.now(),
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('تم المسح وتراكم الكمية بنجاح!'),
                'message': _('المنتج: %s | الكمية السابقة: %s | المضافة: %s | الإجمالي الجديد: %s') % (
                    target_line.product_id.display_name, prev_qty, added_val, new_total
                ),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_open(self):
        self.ensure_one()
        if not self.env.user.has_group('toruq_inventory.group_inventory_count_manager'):
            raise AccessError(_("Only Inventory Managers can open count sessions."))
        if self.state not in ['draft', 'recount_requested']:
            raise UserError(_("Session cannot be opened from state '%s'.") % self.state)

        if self.include_child_locations:
            loc_ids = self.env['stock.location'].search([('id', 'child_of', self.location_id.id)]).ids
        else:
            loc_ids = [self.location_id.id]

        product_domain = [('is_storable', '=', True)]
        if self.product_scope == 'category' and self.category_ids:
            product_domain.append(('categ_id', 'in', self.category_ids.ids))
        elif self.product_scope == 'products' and self.product_ids:
            product_domain.append(('id', 'in', self.product_ids.ids))

        products = self.env['product.product'].search(product_domain)
        if not products:
            raise UserError(_("No storable products match the session scope criteria."))

        if self.state == 'draft':
            self.line_ids.unlink()

            lines_to_create = []
            for prod in products:
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', prod.id),
                    ('location_id', 'in', loc_ids),
                    ('company_id', '=', self.company_id.id)
                ])

                if quants:
                    for q in quants:
                        lines_to_create.append({
                            'session_id': self.id,
                            'product_id': prod.id,
                            'location_id': q.location_id.id,
                            'lot_id': q.lot_id.id if q.lot_id else False,
                            'system_qty_snapshot': q.quantity,
                            'expected_qty_at_count': q.quantity,
                            'is_counted': False,
                            'counted_qty': 0.0,
                        })
                else:
                    lines_to_create.append({
                        'session_id': self.id,
                        'product_id': prod.id,
                        'location_id': self.location_id.id,
                        'lot_id': False,
                        'system_qty_snapshot': 0.0,
                        'expected_qty_at_count': 0.0,
                        'is_counted': False,
                        'counted_qty': 0.0,
                    })

            self.env['foodway.inventory.count.line'].create(lines_to_create)

        new_state = 'recount_in_progress' if self.state == 'recount_requested' else 'opened'
        now = fields.Datetime.now()
        self.write({
            'state': new_state,
            'start_datetime': self.start_datetime or now,
            'opened_by_user_id': self.env.user.id,
        })
        self._create_audit_log('open', _('Session opened for physical counting.'))
        return True

    def action_submit(self):
        self.ensure_one()
        if self.env.user not in self.assigned_user_ids and not self.env.user.has_group('toruq_inventory.group_inventory_count_manager'):
            raise AccessError(_("You are not assigned to submit this session."))
        if self.state not in ['opened', 'recount_in_progress']:
            raise UserError(_("Session cannot be submitted from state '%s'.") % self.state)

        uncounted = self.line_ids.filtered(lambda l: not l.is_counted)
        if uncounted:
            raise UserError(_("Cannot submit session: %d items have not been counted yet.") % len(uncounted))

        now = fields.Datetime.now()
        self.line_ids._recompute_movement_comparison(now)

        self.write({
            'state': 'submitted',
            'submitted_datetime': now,
            'submitted_by_user_id': self.env.user.id,
        })
        self._create_audit_log('submit', _('Session submitted by counter for manager review.'))
        return True

    def action_request_recount(self, reason=None, line_ids=None):
        self.ensure_one()
        if not self.env.user.has_group('toruq_inventory.group_inventory_count_manager'):
            raise AccessError(_("Only Inventory Managers can request a recount."))
        if self.state != 'submitted':
            raise UserError(_("Recount can only be requested for submitted sessions."))

        lines = line_ids if line_ids else self.line_ids
        for line in lines:
            line.write({
                'is_counted': False,
                'recount_history': (line.recount_history or '') + _("\nRound %d: Counted %s at %s by %s") % (
                    self.recount_round + 1,
                    line.counted_qty,
                    line.count_datetime or _('N/A'),
                    line.counted_by_user_id.name if line.counted_by_user_id else _('N/A')
                )
            })

        self.write({
            'state': 'recount_requested',
            'recount_round': self.recount_round + 1,
        })
        msg = _('Recount round %d requested.') % self.recount_round
        if reason:
            msg += _(' Reason: %s') % reason
        self._create_audit_log('recount_request', msg)
        return True

    def action_approve(self):
        self.ensure_one()
        if not self.env.user.has_group('toruq_inventory.group_inventory_count_manager'):
            raise AccessError(_("Only Inventory Managers can approve inventory counts."))

        self.env.cr.execute("SELECT id, state, adjustment_applied FROM foodway_inventory_count_session WHERE id = %s FOR UPDATE", [self.id])
        session_row = self.env.cr.fetchone()
        if not session_row or session_row[1] not in ['submitted'] or session_row[2]:
            raise UserError(_("This session cannot be approved (already approved or invalid state)."))

        now = fields.Datetime.now()
        self.line_ids._recompute_movement_comparison(now)

        created_moves = self.env['stock.move']
        lines_to_adjust = self.line_ids.filtered(lambda l: l.is_counted and l.inventory_difference != 0.0)

        for line in lines_to_adjust:
            if line.product_id.tracking in ['lot', 'serial'] and not line.lot_id:
                raise UserError(_("Cannot adjust product '%s': Lot/Serial number is required for tracked products.") % line.product_id.display_name)

            quant = self.env['stock.quant'].search([
                ('product_id', '=', line.product_id.id),
                ('location_id', '=', line.location_id.id),
                ('company_id', '=', self.company_id.id),
                ('lot_id', '=', line.lot_id.id if line.lot_id else False)
            ], limit=1)

            if not quant:
                quant = self.env['stock.quant'].with_context(inventory_mode=True).create({
                    'product_id': line.product_id.id,
                    'location_id': line.location_id.id,
                    'company_id': self.company_id.id,
                    'lot_id': line.lot_id.id if line.lot_id else False,
                    'quantity': 0.0,
                })

            moves_before = self.env['stock.move'].search([
                ('product_id', '=', line.product_id.id),
                ('company_id', '=', self.company_id.id),
                ('state', '=', 'done')
            ]).ids

            quant = quant.with_context(inventory_mode=True)
            quant.inventory_quantity = line.counted_qty
            quant.user_id = self.env.user.id
            quant.action_apply_inventory()

            new_moves = self.env['stock.move'].search([
                ('product_id', '=', line.product_id.id),
                ('company_id', '=', self.company_id.id),
                ('state', '=', 'done'),
                ('id', 'not in', moves_before)
            ])
            if new_moves:
                new_moves.write({'origin': self.name})
                created_moves |= new_moves

        self.write({
            'state': 'approved',
            'adjustment_applied': True,
            'approved_datetime': now,
            'approved_by_user_id': self.env.user.id,
            'adjustment_move_ids': [(6, 0, created_moves.ids)],
        })
        self._create_audit_log('approved', _('Session approved and %d stock moves executed.') % len(created_moves))
        return True

    def action_cancel(self):
        self.ensure_one()
        if not self.env.user.has_group('toruq_inventory.group_inventory_count_manager'):
            raise AccessError(_("Only Inventory Managers can cancel count sessions."))
        if self.state == 'approved':
            raise UserError(_("Cannot cancel an approved inventory count session."))

        self.write({'state': 'cancelled'})
        self._create_audit_log('cancel', _('Session cancelled.'))
        return True

    def _create_audit_log(self, action, message):
        for session in self:
            self.env['foodway.inventory.count.audit'].create({
                'session_id': session.id,
                'user_id': self.env.user.id,
                'timestamp': fields.Datetime.now(),
                'action': action,
                'message': message,
            })
