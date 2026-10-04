# -*- coding: utf-8 -*-

from odoo import models, fields

class FoodwayInventoryCountMovement(models.Model):
    _name = 'foodway.inventory.count.movement'
    _description = 'Stock Movement Reconciliation Snapshot'
    _order = 'move_date desc, id desc'

    session_id = fields.Many2one('foodway.inventory.count.session', string='Session', required=True, ondelete='cascade', index=True)
    line_id = fields.Many2one('foodway.inventory.count.line', string='Count Line', ondelete='cascade')
    move_id = fields.Many2one('stock.move', string='Stock Move', required=True)
    move_date = fields.Datetime(string='Move Date', related='move_id.date', readonly=True)
    product_id = fields.Many2one(
        'product.product', string='Product', related='move_id.product_id', readonly=True,
        groups='toruq_inventory.group_inventory_count_manager'
    )
    location_id = fields.Many2one(
        'stock.location', string='Source Location', related='move_id.location_id', readonly=True,
        groups='toruq_inventory.group_inventory_count_manager'
    )
    location_dest_id = fields.Many2one(
        'stock.location', string='Destination Location', related='move_id.location_dest_id', readonly=True,
        groups='toruq_inventory.group_inventory_count_manager'
    )
    qty_done = fields.Float(
        string='Quantity Executed', related='move_id.product_uom_qty', readonly=True,
        groups='toruq_inventory.group_inventory_count_manager'
    )
    direction = fields.Selection([
        ('in', 'Incoming (+ Net Stock)'),
        ('out', 'Outgoing (- Net Stock)')
    ], string='Movement Direction', required=True, groups='toruq_inventory.group_inventory_count_manager')
