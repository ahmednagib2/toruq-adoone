# Security Architecture & Blind Protection (`SECURITY.md`)

## Security Principles
1. **Blind Security Enforcement**:
   - `system_qty_snapshot`, `stock_movement_qty`, `expected_qty_at_count`, and `inventory_difference` are strictly hidden from `group_inventory_count_employee`.
   - Field masking is enforced server-side via `read()`, `read_group()`, and `export_data()` overrides in `foodway.inventory.count.line`.
2. **Immutable Audit Trails**:
   - `foodway.inventory.count.audit` and `foodway.inventory.count.entry` prevent `write` and `unlink` at both ACL and Python ORM levels.
3. **Multi-Company & Assignment Isolation**:
   - Record rules enforce company boundaries and limit employee access strictly to assigned count sessions.
4. **Idempotent Stock Adjustment**:
   - Approval executes row-level database locking (`SELECT ... FOR UPDATE`) to prevent concurrent double-approvals.
