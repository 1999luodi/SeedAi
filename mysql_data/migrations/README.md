# SQL Migrations

This directory stores incremental database changes.

## Naming rule
- Use timestamp prefix to keep order stable.
- Format: `YYYYMMDD_HHMM_<short_description>.sql`
- Example: `20260308_1015_create_seed_metrics.sql`

## Workflow
1. Create a new `.sql` file in this directory.
2. Put only the new change in that file (create table/add column/index).
3. Apply migration with `python mysql_data/migrate.py --file <name>.sql`.
4. Commit the migration file.

Current migration example:
- `20260308_1015_create_dataset_label_categories.sql`

## Important
- Never modify an already-applied migration file.
- If logic changes, create a new migration file.
