# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase

class TestBlindInventoryRecount(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestBlindInventoryRecount, cls).setUpClass()
        cls.group_employee = cls.env.ref('toruq_inventory.group_inventory_count_employee')
        cls.group_manager = cls.env.ref('toruq_inventory.group_inventory_count_manager')

        cls.user_employee = cls.env['res.users'].create({
            'name': 'Counter Employee Recount',
            'login': 'counter_emp_recount',
            'email': 'emp_recount@example.com',
            'groups_id': [(6, 0, [cls.group_employee.id])],
        })

        cls.user_manager = cls.env['res.users'].create({
            'name': 'Inventory Manager Recount',
            'login': 'inventory_mgr_recount',
            'email': 'mgr_recount@example.com',
            'groups_id': [(6, 0, [cls.group_manager.id])],
        })

        cls.warehouse = cls.env['stock.warehouse'].search([], limit=1)
        cls.product = cls.env['product.product'].create({
            'name': 'Recount Test Product',
            'is_storable': True,
        })

        cls.session = cls.env['foodway.inventory.count.session'].create({
            'session_name': 'Recount Test Session',
            'warehouse_id': cls.warehouse.id,
            'location_id': cls.warehouse.lot_stock_id.id,
            'assigned_user_ids': [(4, cls.user_employee.id)],
            'product_scope': 'products',
            'product_ids': [(4, cls.product.id)],
        })
        cls.session.action_open()

    def test_01_recount_round_preserves_history(self):
        line = self.session.line_ids[0]
        line.with_user(self.user_employee).action_update_count(10.0, mode='set_total')
        self.session.with_user(self.user_employee).action_submit()

        wizard = self.env['foodway.inventory.count.recount.wizard'].with_user(self.user_manager).create({
            'session_id': self.session.id,
            'recount_scope': 'all',
            'reason': 'Discrepancy detected in round 1',
        })
        wizard.action_process_recount()

        self.assertEqual(self.session.state, 'recount_requested')
        self.assertEqual(self.session.recount_round, 1)
        self.assertIn('10.0', line.recount_history)

        self.session.action_open()
        line.with_user(self.user_employee).action_update_count(8.0, mode='set_total')
        self.assertEqual(line.counted_qty, 8.0)
