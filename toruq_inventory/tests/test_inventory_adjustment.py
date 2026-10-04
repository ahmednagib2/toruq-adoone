# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

class TestBlindInventoryAdjustment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestBlindInventoryAdjustment, cls).setUpClass()
        cls.group_manager = cls.env.ref('toruq_inventory.group_inventory_count_manager')
        cls.group_employee = cls.env.ref('toruq_inventory.group_inventory_count_employee')

        cls.user_manager = cls.env['res.users'].create({
            'name': 'Manager Adjust User',
            'login': 'mgr_adjust',
            'email': 'mgr_adj@example.com',
            'groups_id': [(6, 0, [cls.group_manager.id])],
        })

        cls.user_employee = cls.env['res.users'].create({
            'name': 'Employee Adjust User',
            'login': 'emp_adjust',
            'email': 'emp_adj@example.com',
            'groups_id': [(6, 0, [cls.group_employee.id])],
        })

        cls.warehouse = cls.env['stock.warehouse'].search([], limit=1)
        cls.product = cls.env['product.product'].create({
            'name': 'Adjustment Product',
            'is_storable': True,
        })

        cls.session = cls.env['foodway.inventory.count.session'].create({
            'session_name': 'Adjustment Session',
            'warehouse_id': cls.warehouse.id,
            'location_id': cls.warehouse.lot_stock_id.id,
            'assigned_user_ids': [(4, cls.user_employee.id)],
            'product_scope': 'products',
            'product_ids': [(4, cls.product.id)],
        })
        cls.session.action_open()

    def test_01_idempotent_approval(self):
        line = self.session.line_ids[0]
        line.with_user(self.user_employee).action_update_count(15.0, mode='set_total')
        self.session.with_user(self.user_employee).action_submit()

        self.session.with_user(self.user_manager).action_approve()
        self.assertTrue(self.session.adjustment_applied)
        self.assertEqual(self.session.state, 'approved')

        with self.assertRaises(UserError):
            self.session.with_user(self.user_manager).action_approve()
