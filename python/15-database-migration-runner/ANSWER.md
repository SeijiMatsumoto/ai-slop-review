# 15 — Database Migration Runner (Python)

**Categories:** SQL Injection, Data Integrity, Concurrency

## Bug 1: SQL Injection via Filename

In `run_migration`, the migration filename is recorded using string formatting directly into SQL:

```python
self.conn.execute(
    "INSERT INTO schema_migrations (filename) VALUES ('%s')" % filename
)
```

A maliciously named file like `001'); DROP TABLE users; --.sql` would inject arbitrary SQL. Since migration filenames come from the filesystem, anyone with write access to the migrations directory can exploit this.

**Fix:** Use parameterized queries:

```python
self.conn.execute(
    "INSERT INTO schema_migrations (filename) VALUES (?)", (filename,)
)
```

## Bug 2: No Transaction Wrapping — Partial Migrations

Each statement within a migration is executed individually, and `conn.commit()` is called only once at the end. If the third statement in a 5-statement migration fails, the first two statements have already been executed on the connection (SQLite auto-commits DDL in some cases, and the state is left inconsistent). There is no transaction wrapping to ensure the entire migration either fully applies or fully rolls back.

**Fix:** Wrap each migration in an explicit transaction:

```python
try:
    self.conn.execute("BEGIN")
    for statement in statements:
        if statement.strip():
            self.conn.execute(statement)
    self.conn.execute(
        "INSERT INTO schema_migrations (filename) VALUES (?)", (filename,)
    )
    self.conn.commit()
except Exception:
    self.conn.rollback()
    raise
```

## Bug 3: Migration Ordering Is Alphabetical String Sort, Not Numeric

`discover_migrations` uses `sorted(files)` which does lexicographic (string) sorting. This means a migration named `10-add-index.sql` sorts before `2-create-table.sql` because the character `"1"` comes before `"2"`. Migrations will run in the wrong order, potentially failing or corrupting the schema.

**Fix:** Sort numerically by extracting the leading number:

```python
def _sort_key(filepath):
    filename = os.path.basename(filepath)
    num = int(filename.split("-")[0].split("_")[0])
    return num

migration_files = sorted(files, key=_sort_key)
```

## Bug 4: No Locking — Concurrent Migrations Corrupt State

There is no file lock or database lock to prevent two instances of the migration runner from executing simultaneously. If two processes run `run_pending()` at the same time, both will see the same pending migrations and attempt to run them, leading to duplicate executions, constraint violations, or corrupted schema state.

**Fix:** Use an advisory lock (file lock or database-level lock) before running migrations:

```python
import fcntl

lock_file = open(os.path.join(self.migrations_dir, ".migration.lock"), "w")
fcntl.flock(lock_file, fcntl.LOCK_EX)
# ... run migrations ...
fcntl.flock(lock_file, fcntl.LOCK_UN)
```

## Bug 5: Rollback Executes Entire SQL File as One Statement

In `rollback_last`, the entire rollback file content is executed as a single statement:

```python
self.conn.execute(sql_content)
```

If the rollback file contains multiple SQL statements separated by semicolons, only the first statement will execute (or it will fail entirely). This is inconsistent with how `run_migration` splits on semicolons, and means rollbacks will silently be incomplete.

**Fix:** Split and execute statements the same way as `run_migration`, and wrap in a transaction.
