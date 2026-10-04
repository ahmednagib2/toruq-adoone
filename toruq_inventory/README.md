# Blind Inventory Count / الجرد الأعمى (`toruq_inventory`)

Production-Grade Blind Physical Inventory Counting System for Odoo 18 Enterprise.

## Features
- **Blind Counting UI**: Restricts counters and cashiers from seeing theoretical stock levels, snapshot quantities, valuation impact, or inventory discrepancies.
- **Fail-Closed Server Security**: Overrides ORM `read()`, `read_group()`, `search_read()`, and `export_data()` to strip or block confidential stock fields for non-managers.
- **Batch Movement Reconciliation Engine**: Computes net stock movements between count initiation and review across target location boundaries in optimized single-pass batch queries.
- **Honeywell Handheld Mobile Terminal**: Optimized for Honeywell Android handheld barcode scanners (Keyboard Wedge) with rapid touch preset buttons (1, 2, 5, 10, 12, 24, 50) and auto-clearing barcode inputs.
- **Immutable Audit Logs**: Append-only execution logs (`foodway.inventory.count.audit` and `foodway.inventory.count.entry`) with server-side write/unlink protection.
- **Multi-Company & Multi-Warehouse**: Strict company isolation and assignment record rules.
- **Idempotent Stock Adjustment**: Transaction-safe row locking (`SELECT FOR UPDATE`) preventing race conditions and duplicate approvals.

## Module Structure
- `models/`: Session, Line, Entry, Audit, and Movement reconciliation logic.
- `wizard/`: Structured Recount Wizard.
- `report/`: Excel Manager Audit Export Wizard.
- `security/`: ACLs, security groups, and record rules.
- `views/`: Mobile terminal, session management, and manager views.
- `tests/`: Security, concurrency, adjustment, recount, and movement reconciliation unit tests.
