# -*- coding: utf-8 -*-

import io
import base64
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

class FoodwayInventoryCountReportWizard(models.TransientModel):
    _name = 'foodway.inventory.count.report.wizard'
    _description = 'Blind Inventory Manager Excel Report Wizard'

    session_id = fields.Many2one('foodway.inventory.count.session', string='Session')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    location_id = fields.Many2one('stock.location', string='Location')
    date_from = fields.Datetime(string='Date From')
    date_to = fields.Datetime(string='Date To')
    only_discrepancies = fields.Boolean(string='Discrepancies Only', default=False)

    excel_file = fields.Binary(string='Excel Report File', readonly=True)
    filename = fields.Char(string='Filename', readonly=True)

    def action_export_excel(self):
        self.ensure_one()
        if not self.env.user.has_group('toruq_inventory.group_inventory_count_manager'):
            raise AccessError(_("Only Inventory Managers can export detailed stock inventory reports."))

        if not xlsxwriter:
            raise UserError(_("Python 'xlsxwriter' library is required to generate Excel reports."))

        domain = [('company_id', 'in', self.env.companies.ids)]
        if self.session_id:
            domain.append(('session_id', '=', self.session_id.id))
        if self.warehouse_id:
            domain.append(('session_id.warehouse_id', '=', self.warehouse_id.id))
        if self.location_id:
            domain.append(('location_id', '=', self.location_id.id))
        if self.date_from:
            domain.append(('session_id.start_datetime', '>=', self.date_from))
        if self.date_to:
            domain.append(('session_id.start_datetime', '<=', self.date_to))
        if self.only_discrepancies:
            domain.extend([('is_counted', '=', True), ('inventory_difference', '!=', 0)])

        lines = self.env['foodway.inventory.count.line'].search(domain)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Blind Inventory Audit')

        # Formatting Styles
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#1f4e78', 'font_color': '#ffffff',
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        cell_format = workbook.add_format({'border': 1, 'align': 'left'})
        num_format = workbook.add_format({'border': 1, 'align': 'right', 'num_format': '#,##0.00'})
        diff_warning_format = workbook.add_format({'border': 1, 'align': 'right', 'bg_color': '#ffc7ce', 'font_color': '#9c0006', 'num_format': '#,##0.00'})

        headers = [
            'Session Reference', 'Warehouse', 'Location', 'Product Code / Barcode',
            'Product Name', 'Lot / Serial', 'Count Status', 'Counter Employee',
            'Count Timestamp', 'Physical Count Qty', 'Initial Snapshot Qty',
            'Net Movements Qty', 'Expected Qty at Count', 'Discrepancy Qty'
        ]

        worksheet.row_dimensions[0].height = 25
        for col_idx, text in enumerate(headers):
            worksheet.write(0, col_idx, text, header_format)
            worksheet.set_column(col_idx, col_idx, 18)

        row_idx = 1
        for line in lines:
            diff = line.inventory_difference
            qty_fmt = diff_warning_format if (line.is_counted and diff != 0) else num_format

            worksheet.write(row_idx, 0, line.session_id.name or '', cell_format)
            worksheet.write(row_idx, 1, line.session_id.warehouse_id.name or '', cell_format)
            worksheet.write(row_idx, 2, line.location_id.display_name or '', cell_format)
            worksheet.write(row_idx, 3, line.barcode or line.product_id.default_code or '', cell_format)
            worksheet.write(row_idx, 4, line.product_id.display_name or '', cell_format)
            worksheet.write(row_idx, 5, line.lot_id.name if line.lot_id else '', cell_format)
            worksheet.write(row_idx, 6, 'Counted' if line.is_counted else 'Uncounted', cell_format)
            worksheet.write(row_idx, 7, line.counted_by_user_id.name if line.counted_by_user_id else '', cell_format)
            worksheet.write(row_idx, 8, str(line.count_datetime) if line.count_datetime else '', cell_format)
            worksheet.write(row_idx, 9, line.counted_qty, num_format)
            worksheet.write(row_idx, 10, line.system_qty_snapshot, num_format)
            worksheet.write(row_idx, 11, line.stock_movement_qty, num_format)
            worksheet.write(row_idx, 12, line.expected_qty_at_count, num_format)
            worksheet.write(row_idx, 13, diff, qty_fmt)
            row_idx += 1

        workbook.close()
        output.seek(0)
        file_data = output.read()
        output.close()

        fname = 'Blind_Inventory_Audit_Report_%s.xlsx' % fields.Date.today()
        self.write({
            'excel_file': base64.b64encode(file_data),
            'filename': fname,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=%s&id=%s&field=excel_file&download=true&filename=%s' % (self._name, self.id, fname),
            'target': 'self',
        }
