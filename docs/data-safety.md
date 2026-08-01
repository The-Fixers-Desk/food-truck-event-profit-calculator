# Data safety

Customer backups use the `.ftbackup` extension and are ZIP-compatible. Each
archive contains only `database.sqlite` and `manifest.json`. Format Version 1
records the application and schema versions, UTC creation time, internal
database filename, backup kind, and SHA-256 database checksum.

Backups use SQLite's connection backup API rather than copying the live file.
The snapshot must pass SQLite integrity and foreign-key checks before it is
packaged. Uploads are size-limited and staged beneath the configured
application-data root. Restore accepts exactly the two expected archive
members, never trusts archive paths, validates the manifest and checksum,
checks SQLite integrity and relationships, and migrates an older supported
database only in staging.

Because profile and notification records live in the same versioned SQLite
database, a full export and import includes them. Resetting Business Defaults
or deleting saved Events preserves both. Clearing all app data removes both,
along with the persisted last-export marker.

Restore is complete replacement, not a merge. After staged validation the app
creates a validated pre-restore recovery snapshot, closes the live connection,
atomically replaces the database, reopens and verifies it, and checks normal
repository access. A replacement or post-check failure applies the validated
recovery snapshot. In startup recovery mode, the unreadable original is moved
intact to the recovery directory before the validated restore is installed.

Before a pending production migration, startup creates a validated
pre-migration snapshot. No snapshot is created for an already-current
database. Automatic snapshots are stored in `automatic-recovery` and only the
five newest managed `recovery-*.ftbackup` files are retained. Unrelated files
and downloaded customer backups are never pruned. Cleanup failure is logged
but does not invalidate a successfully created snapshot.

`ApplicationDataPaths` owns the live database, staging, temporary, and
automatic-recovery locations. Tests and future desktop packages should set
`DATA_ROOT`; when they do, the database defaults to `DATA_ROOT/app.db`.
Development remains compatible with `data/app.db`. Platform-specific desktop
packaging should choose the external per-user root and must not place mutable
data beside packaged application files.
