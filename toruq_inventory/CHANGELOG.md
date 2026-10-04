# Changelog (`CHANGELOG.md`)

## [18.0.1.0.0] - 2026-10-04
### Added
- Dedicated Honeywell Handheld Mobile Terminal UI with touch quantity preset buttons.
- Batch Movement Reconciliation Engine calculating net stock changes without N+1 query overhead.
- Fail-closed security overrides on `read_group()` and `export_data()` for `foodway.inventory.count.line`.
- Immutable audit trail protections on `foodway.inventory.count.audit` and `foodway.inventory.count.entry`.
- Comprehensive test suite including security, concurrency, adjustment, recount, and movement reconciliation tests.

### Fixed
- Resolved Odoo 18 view validation error by replacing unbound label tags with `<span class="o_form_label">`.
- Enforced explicit short relation names for all `Many2many` fields to comply with PostgreSQL 63-character table name limit.
- Added explicit date and warehouse filtering to Excel report export wizard.
