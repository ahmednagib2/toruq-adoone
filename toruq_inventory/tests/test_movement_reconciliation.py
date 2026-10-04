# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.fields import Datetime

class TestBlindInventoryMovementReconciliation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestBlindInventoryMovementReconciliation, cls).setUpClass()
        cls.group_manager = cls.env.ref('toruq_inventory.group_inventory_count_manager')
        cls.group_employee = cls.env.ref('toruq_inventory.group_inventory_count_employee')

        cls.user_manager = cls.env['res.users'].create({
            'name': 'Movement Manager User',
            'login': 'mgr_movement',
            'email': 'mgr_mov@example.com',
            'groups_id': [(6, 0, [cls.group_manager.id])],
        })

        cls.user_employee = cls.env['res.users'].create({
            'name': 'Movement Employee User',
            'login': 'emp_movement',
            'email': 'emp_mov@example.com',
            'groups_id': [(6, 0, [cls.group_employee.id])],
        })

        cls.warehouse = cls.env['stock.warehouse'].search([], limit=1)
        cls.location = cls.warehouse.lot_stock_id

        cls.product = cls.env['product.product'].create({
            'name': 'Movement Test Product',
            'is_storable': True,
        })

        cls.session = cls.env['foodway.inventory.count.session'].create({
            'session_name': 'Movement Test Session',
            'warehouse_id': cls.warehouse.id,
            'location_id': cls.location.id,
            'assigned_user_ids': [(4, cls.user_employee.id)],
            'product_scope': 'products',
            'product_ids': [(4, cls.product.id)],
        })
        cls.session.action_open()

    def test_01_movement_calculation(self):
        line = self.session.line_ids[0]
        # Recompute movements
        line._batch_recompute_movement_comparison()
        self.assertEqual(line.stock_movement_qty, 0.0)
        self.assertEqual(line.expected_qty_at_count, line.system_qty_snapshot)
