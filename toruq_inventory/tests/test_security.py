# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError, UserError

class TestBlindInventorySecurity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestBlindInventorySecurity, cls).setUpClass()
        cls.group_employee = cls.env.ref('toruq_inventory.group_inventory_count_employee')
        cls.group_manager = cls.env.ref('toruq_inventory.group_inventory_count_manager')

        cls.user_employee = cls.env['res.users'].create({
            'name': 'Counter Employee User',
            'login': 'counter_emp_sec',
            'email': 'emp_sec@example.com',
            'groups_id': [(6, 0, [cls.group_employee.id])],
        })

        cls.user_manager = cls.env['res.users'].create({
            'name': 'Inventory Manager User',
            'login': 'inventory_mgr_sec',
            'email': 'mgr_sec@example.com',
            'groups_id': [(6, 0, [cls.group_manager.id])],
        })

        cls.warehouse = cls.env['stock.warehouse'].search([], limit=1)
        cls.product = cls.env['product.product'].create({
            'name': 'Security Test Product',
            'is_storable': True,
        })

        cls.session = cls.env['foodway.inventory.count.session'].create({
            'session_name': 'Security Test Session',
            'warehouse_id': cls.warehouse.id,
            'location_id': cls.warehouse.lot_stock_id.id,
            'assigned_user_ids': [(4, cls.user_employee.id)],
            'product_scope': 'products',
            'product_ids': [(4, cls.product.id)],
        })
        cls.session.action_open()

    def test_01_employee_cannot_read_confidential_fields(self):
        line = self.session.line_ids[0]
        line.with_user(self.user_employee).action_update_count(10.0, mode='set_total')
        res = line.with_user(self.user_employee).read(['product_id', 'counted_qty', 'system_qty_snapshot', 'inventory_difference'])[0]

        self.assertEqual(res['counted_qty'], 10.0)
        self.assertFalse(res['system_qty_snapshot'])
        self.assertFalse(res['inventory_difference'])

    def test_02_manager_can_read_confidential_fields(self):
        line = self.session.line_ids[0]
        res = line.with_user(self.user_manager).read(['system_qty_snapshot', 'inventory_difference'])[0]
        self.assertIsNotNone(res['system_qty_snapshot'])

    def test_03_employee_cannot_approve_session(self):
        self.session.with_user(self.user_employee).line_ids[0].action_update_count(5.0, mode='set_total')
        self.session.with_user(self.user_employee).action_submit()
        with self.assertRaises(AccessError):
            self.session.with_user(self.user_employee).action_approve()

    def test_04_employee_cannot_read_group_confidential_fields(self):
        with self.assertRaises(AccessError):
            self.env['foodway.inventory.count.line'].with_user(self.user_employee).read_group(
                [('session_id', '=', self.session.id)],
                ['inventory_difference:sum'],
                ['product_id']
            )

    def test_05_employee_cannot_export_confidential_fields(self):
        line = self.session.line_ids[0]
        with self.assertRaises(AccessError):
            line.with_user(self.user_employee).export_data(['product_id', 'system_qty_snapshot', 'inventory_difference'])

    def test_06_audit_log_immutability(self):
        audit = self.env['foodway.inventory.count.audit'].create({
            'session_id': self.session.id,
            'user_id': self.user_manager.id,
            'action': 'TEST_ACTION',
            'message': 'Test audit message',
        })
        with self.assertRaises(UserError):
            audit.with_user(self.user_manager).write({'message': 'Tampered message'})
        with self.assertRaises(UserError):
            audit.with_user(self.user_manager).unlink()
