# Database migrations

Version 1 is the complete schema established before formal versioning:
Business Defaults and their ordered labor rows, Events, Event Scenarios, and
ordered scenario labor and additional-cost rows. Money uses cents,
percentages use basis points, and paid time uses minutes.

Applied versions are stored once in `schema_migrations`. Startup reads this
ledger from SQLite, applies every missing migration in order, verifies it, and
records it last in the same transaction. Never edit a released migration.

To add a migration:

1. Increase `LATEST_SUPPORTED_SCHEMA_VERSION`.
2. Add the next sequential immutable `Migration` to `MIGRATIONS`.
3. Make its apply function validate its starting assumptions and change only
   that version's schema.
4. Make its verify function check the resulting schema, data, relationships,
   integrity, and copied row counts.
5. Add upgrade, rollback, restart, and data-preservation tests.

Migration functions must not commit. The runner owns the transaction and
rolls back the schema, copied data, and ledger entry together on failure.

For table reconstruction, use a unique version-specific temporary name such
as `event_scenarios_migration_v2`. Fail if that name already exists. Create
the new table explicitly, copy named columns explicitly, verify row counts and
relationships, then replace the original. Do not reuse or silently delete an
unexpected temporary table.

A compatible unversioned database is checked for the complete Version 1
tables, columns and types, important indexes and foreign keys, SQLite
integrity, and foreign-key consistency before it is stamped Version 1. Its
business rows, identifiers, ordering, and timestamps are not rewritten.
Incomplete, conflicting, damaged, and future-version databases are rejected
without destructive repair or downgrade.

The final recognized pre-ledger Defaults-only schema is a narrow compatibility
case. It is upgraded transactionally with migration-specific temporary table
names, explicit column copies, and row-count verification before Version 1 is
recorded. Other incomplete or unknown shapes are rejected.
