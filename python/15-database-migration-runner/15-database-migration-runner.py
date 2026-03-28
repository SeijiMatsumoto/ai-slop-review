# AI-generated PR — review this code
# Description: "Added database migration runner that discovers and executes .sql migration files"

import os
import sqlite3
import glob
import time
from datetime import datetime


class MigrationRunner:
    """Discovers and runs SQL migration files against a SQLite database."""

    def __init__(self, db_path: str, migrations_dir: str):
        self.db_path = db_path
        self.migrations_dir = migrations_dir
        self.conn = sqlite3.connect(db_path)
        self._ensure_migration_table()

    def _ensure_migration_table(self):
        """Create the migrations tracking table if it doesn't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def get_applied_migrations(self) -> set:
        """Return the set of already-applied migration filenames."""
        cursor = self.conn.execute("SELECT filename FROM schema_migrations")
        return {row[0] for row in cursor.fetchall()}

    def discover_migrations(self) -> list:
        """Find all .sql files in the migrations directory, sorted by name."""
        pattern = os.path.join(self.migrations_dir, "*.sql")
        files = glob.glob(pattern)
        migration_files = sorted(files)
        return migration_files

    def run_migration(self, filepath: str):
        """Execute a single migration file."""
        filename = os.path.basename(filepath)
        print(f"[{datetime.now()}] Running migration: {filename}")

        with open(filepath, "r") as f:
            sql_content = f.read()

        # Execute each statement in the migration file
        statements = sql_content.split(";")
        for statement in statements:
            statement = statement.strip()
            if statement:
                self.conn.execute(statement)

        # Record the migration as applied
        self.conn.execute(
            "INSERT INTO schema_migrations (filename) VALUES ('%s')" % filename
        )
        self.conn.commit()
        print(f"[{datetime.now()}] Completed: {filename}")

    def run_pending(self):
        """Run all pending migrations in order."""
        applied = self.get_applied_migrations()
        all_migrations = self.discover_migrations()

        pending = [m for m in all_migrations if os.path.basename(m) not in applied]

        if not pending:
            print("No pending migrations found.")
            return

        print(f"Found {len(pending)} pending migration(s).")

        for migration in pending:
            self.run_migration(migration)

        print("All migrations applied successfully.")

    def get_status(self) -> list:
        """Show the status of all migrations."""
        applied = self.get_applied_migrations()
        all_migrations = self.discover_migrations()

        status = []
        for migration in all_migrations:
            filename = os.path.basename(migration)
            status.append({
                "filename": filename,
                "applied": filename in applied,
            })
        return status

    def rollback_last(self):
        """Rollback the most recently applied migration."""
        cursor = self.conn.execute(
            "SELECT filename FROM schema_migrations ORDER BY id DESC LIMIT 1"
        )
        last = cursor.fetchone()

        if not last:
            print("No migrations to rollback.")
            return

        filename = last[0]
        rollback_file = os.path.join(
            self.migrations_dir, filename.replace(".sql", "_rollback.sql")
        )

        if not os.path.exists(rollback_file):
            print(f"No rollback file found for {filename}. Cannot rollback.")
            return

        with open(rollback_file, "r") as f:
            sql_content = f.read()

        self.conn.execute(sql_content)
        self.conn.execute(
            "DELETE FROM schema_migrations WHERE filename = ?", (filename,)
        )
        self.conn.commit()
        print(f"Rolled back: {filename}")

    def close(self):
        """Close the database connection."""
        self.conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python migration_runner.py <command> [db_path] [migrations_dir]")
        print("Commands: run, status, rollback")
        sys.exit(1)

    command = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else "app.db"
    migrations_dir = sys.argv[3] if len(sys.argv) > 3 else "./migrations"

    runner = MigrationRunner(db_path, migrations_dir)

    if command == "run":
        runner.run_pending()
    elif command == "status":
        for entry in runner.get_status():
            mark = "x" if entry["applied"] else " "
            print(f"  [{mark}] {entry['filename']}")
    elif command == "rollback":
        runner.rollback_last()
    else:
        print(f"Unknown command: {command}")

    runner.close()
