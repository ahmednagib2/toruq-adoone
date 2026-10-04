# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase

class TestBlindInventoryConcurrency(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestBlindInventoryConcurrency, cls).setUpClass()
        cls.group_employee = cls.env.ref('toruq_inventory.group_inventory_count_employee')

        cls.user_employee = cls.env['res.users'].create({
            'name': 'Concurrency Employee User',
            'login': 'emp_concur',
            'email': 'emp_concur@example.com',
            'groups_id': [(6, 0, [cls.group_employee.id])],
        })

        cls.warehouse = cls.env['stock.warehouse'].search([], limit=1)
        cls.product = cls.env['product.product'].create({
            'name': 'Concurrency Product',
            'is_storable': True,
        })

        cls.session = cls.env['foodway.inventory.count.session'].create({
            'session_name': 'Concurrency Session',
            'warehouse_id': cls.warehouse.id,
            'location_id': cls.warehouse.lot_stock_id.id,
            'assigned_user_ids': [(4, cls.user_employee.id)],
            'product_scope': 'products',
            'product_ids': [(4, cls.product.id)],
        })
        cls.session.action_open()

    def test_01_rapid_scan_entry_logging(self):
        line = self.session.line_ids[0]
        for i in range(5):
            line.with_user(self.user_employee).action_update_count(1.0, mode='add')

        self.assertEqual(line.counted_qty, 5.0)
        entries = self.env['foodway.inventory.count.entry'].search([('line_id', '=', line.id)])
        self.assertEqual(len(entries), 5)
