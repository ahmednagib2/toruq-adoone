# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase

class TestBlindInventoryCounting(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestBlindInventoryCounting, cls).setUpClass()
        cls.group_employee = cls.env.ref('toruq_inventory.group_inventory_count_employee')
        cls.group_manager = cls.env.ref('toruq_inventory.group_inventory_count_manager')

        cls.user_employee = cls.env['res.users'].create({
            'name': 'Counter Employee',
            'login': 'counter_emp_count',
            'email': 'emp_count@example.com',
            'groups_id': [(6, 0, [cls.group_employee.id])],
        })

        cls.warehouse = cls.env['stock.warehouse'].search([], limit=1)
        cls.product = cls.env['product.product'].create({
            'name': 'Counting Test Product',
            'is_storable': True,
        })

        cls.session = cls.env['foodway.inventory.count.session'].create({
            'session_name': 'Counting Test Session',
            'warehouse_id': cls.warehouse.id,
            'location_id': cls.warehouse.lot_stock_id.id,
            'assigned_user_ids': [(4, cls.user_employee.id)],
            'product_scope': 'products',
            'product_ids': [(4, cls.product.id)],
        })
        cls.session.action_open()

    def test_01_add_mode_quantity(self):
        line = self.session.line_ids[0]
        line.with_user(self.user_employee).action_update_count(5.0, mode='add')
        self.assertEqual(line.counted_qty, 5.0)

        line.with_user(self.user_employee).action_update_count(5.0, mode='add')
        self.assertEqual(line.counted_qty, 10.0)

    def test_02_set_total_mode_quantity(self):
        line = self.session.line_ids[0]
        line.with_user(self.user_employee).action_update_count(10.0, mode='set_total')
        self.assertEqual(line.counted_qty, 10.0)

        line.with_user(self.user_employee).action_update_count(8.0, mode='set_total')
        self.assertEqual(line.counted_qty, 8.0)
