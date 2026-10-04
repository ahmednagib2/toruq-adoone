# MODULE RENAME REPORT (RENAME_REPORT.md)

**Old Module Name:** `foodway_blind_inventory_count`  
**New Module Name:** `toruq_inventory`  
**Display Name:** `الجرد الأعمى / Blind Inventory Count`  
**Author:** `ahmednagib`  
**Developer:** `Ahmed Nagib`  

---

## 1. Mechanical Rename Summary
- **Folder Path**: Renamed from `D:\odoo طرق الغزاء\invntory\foodway_blind_inventory_count` to `D:\odoo طرق الغزاء\invntory\toruq_inventory`.
- **Namespace Updates**: Updated all XML IDs, security groups, ORM group checks (`groups='toruq_inventory.group_inventory_count_manager'`), view XML references, action definitions, sequence declarations, report definitions, menu items, and unit test imports.
- **ORM Model Names**: Preserved intact (`foodway.inventory.count.session`, `foodway.inventory.count.line`, `foodway.inventory.count.entry`, `foodway.inventory.count.audit`, `foodway.inventory.count.movement`, `foodway.inventory.count.recount.wizard`, `foodway.inventory.count.report.wizard`) per strict instruction #5.

---

## 2. Status & Verification Matrix

```text
Old Module Name:
foodway_blind_inventory_count

New Module Name:
toruq_inventory

Display Name:
الجرد الأعمى / Blind Inventory Count

ORM Model Names Changed:
NO

Business Logic Changed:
NO

Security Logic Changed:
NO

Inventory Logic Changed:
NO

Tests Changed:
Only paths/references required for rename

ZIP Created:
YES

GitHub Push:
SUCCESS

Repository:
https://github.com/ahmednagib2/toruq-adoone.git

Branch:
feature/toruq-inventory

Commit SHA:
1518806957fdd728f1b3acdf22cd8871677ec6fd

Original Table Name Error:
Renaming the addon folder from foodway_blind_inventory_count to toruq_inventory did not alter the ORM model names (foodway.inventory.count.line & foodway.inventory.count.recount.wizard). Therefore, PostgreSQL join table name generation remains derived from ORM model names.

Does renaming the addon resolve the long table-name error:
NO (Additional schema-level relation name parameter is required for that Many2many field if ORM model names are preserved without modification).
```
