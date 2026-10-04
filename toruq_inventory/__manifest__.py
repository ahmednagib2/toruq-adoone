# -*- coding: utf-8 -*-
{
    'name': 'الجرد الأعمى / Blind Inventory Count',
    'summary': 'Blind physical inventory counting system for handheld Honeywell barcode scanners in Odoo 18 Enterprise.',
    'description': """
Blind Inventory Count System for Odoo 18 Enterprise
===================================================
- Prevents counters and cashiers from seeing theoretical stock levels.
- Full server-side security restricting confidential inventory quantities and valuations.
- Movement-aware reconciliation calculating net stock changes during count execution.
- Optimized for Honeywell Android handheld barcode scanners (Keyboard Wedge).
- Multi-company and multi-warehouse support.
- Comprehensive Manager Excel exports and recount workflows.
    """,
    'author': 'ahmednagib',
    'website': 'https://foodway.sa',
    'category': 'Inventory/Inventory',
    'version': '18.0.1.0.0',
    'license': 'OPL-1',
    'depends': [
        'base',
        'stock',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'data/sequence.xml',
        'views/inventory_count_session_views.xml',
        'views/inventory_count_line_views.xml',
        'views/inventory_count_employee_views.xml',
        'views/inventory_count_manager_views.xml',
        'views/inventory_count_menus.xml',
        'wizard/recount_wizard_views.xml',
        'report/inventory_count_report_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
