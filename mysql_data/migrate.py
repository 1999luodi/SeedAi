"""
SeedAI SQL migration runner.

Goal:
- Add/alter schema via independent SQL files.
- Avoid editing init_db.sql for every schema change.
"""

import argparse
import hashlib
import importlib
import os
from pathlib import Path
from typing import List, Tuple

pymysql = None

BASE_DIR = Path(__file__).resolve().parent
MIGRATIONS_DIR = BASE_DIR / "migrations"


def get_db_connection(database: str | None = None):
    global pymysql
    if pymysql is None:
        try:
            pymysql = importlib.import_module("pymysql")
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "Missing dependency: pymysql. Install backend requirements or run in backend container."
            ) from exc
    if pymysql is None:
        raise RuntimeError(
            "Missing dependency: pymysql. Install backend requirements or run in backend container."
        )
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "mysql"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "rootpass"),
        database=database,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )


def ensure_database_and_history_table() -> None:
    db_name = os.getenv("MYSQL_DATABASE", "ai_dataset")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cursor.execute(f"USE `{db_name}`;")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    migration_name VARCHAR(255) NOT NULL UNIQUE,
                    migration_hash CHAR(64) NOT NULL,
                    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    execution_ms INT NOT NULL DEFAULT 0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
        conn.commit()
    finally:
        conn.close()


def list_sql_files() -> List[Path]:
    if not MIGRATIONS_DIR.exists():
        return []
    files = [p for p in MIGRATIONS_DIR.iterdir() if p.is_file() and p.suffix.lower() == ".sql"]
    return sorted(files, key=lambda p: p.name)


def get_file_hash(file_path: Path) -> str:
    content = file_path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def get_applied_migrations() -> dict:
    db_name = os.getenv("MYSQL_DATABASE", "ai_dataset")
    conn = get_db_connection(db_name)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT migration_name, migration_hash FROM schema_migrations;")
            rows = cursor.fetchall()
            return {row["migration_name"]: row["migration_hash"] for row in rows}
    finally:
        conn.close()


def split_sql_statements(sql: str) -> List[str]:
    statements = []
    current = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(current).strip().rstrip(";"))
            current = []
    if current:
        statements.append("\n".join(current).strip())
    return [stmt for stmt in statements if stmt]


def execute_migration(file_path: Path) -> Tuple[bool, str]:
    import time

    db_name = os.getenv("MYSQL_DATABASE", "ai_dataset")
    migration_name = file_path.name
    migration_hash = get_file_hash(file_path)

    conn = get_db_connection(db_name)
    try:
        start = time.perf_counter()
        sql = file_path.read_text(encoding="utf-8")
        statements = split_sql_statements(sql)

        with conn.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)

            elapsed_ms = int((time.perf_counter() - start) * 1000)
            cursor.execute(
                """
                INSERT INTO schema_migrations (migration_name, migration_hash, execution_ms)
                VALUES (%s, %s, %s)
                """,
                (migration_name, migration_hash, elapsed_ms),
            )

        conn.commit()
        return True, f"applied in {elapsed_ms}ms"
    except Exception as exc:
        conn.rollback()
        return False, str(exc)
    finally:
        conn.close()


def pending_migrations(files: List[Path], applied: dict) -> List[Path]:
    pending = []
    for file_path in files:
        if file_path.name not in applied:
            pending.append(file_path)
            continue
        current_hash = get_file_hash(file_path)
        if applied[file_path.name] != current_hash:
            raise RuntimeError(
                f"Migration hash mismatch: {file_path.name}. "
                "Do not edit applied migration files; create a new one instead."
            )
    return pending


def main():
    parser = argparse.ArgumentParser(description="Run SeedAI SQL migrations")
    parser.add_argument("--all", action="store_true", help="Apply all pending migrations")
    parser.add_argument("--file", type=str, help="Apply a single migration file by name")
    parser.add_argument("--status", action="store_true", help="Show migration status only")
    args = parser.parse_args()

    if not args.all and not args.file and not args.status:
        parser.print_help()
        return

    ensure_database_and_history_table()

    files = list_sql_files()
    applied = get_applied_migrations()

    if args.status:
        print("Migration status:")
        for file_path in files:
            state = "APPLIED" if file_path.name in applied else "PENDING"
            print(f"- [{state}] {file_path.name}")
        return

    if args.file:
        target = MIGRATIONS_DIR / args.file
        if not target.exists() or target.suffix.lower() != ".sql":
            raise FileNotFoundError(f"Migration file not found: {target}")

        if target.name in applied:
            current_hash = get_file_hash(target)
            if applied[target.name] == current_hash:
                print(f"Skip: {target.name} already applied")
                return
            raise RuntimeError(
                f"Migration hash mismatch: {target.name}. "
                "This file was already applied but has changed."
            )

        ok, message = execute_migration(target)
        if not ok:
            raise RuntimeError(f"Failed: {target.name} -> {message}")
        print(f"Success: {target.name} ({message})")
        return

    if args.all:
        pendings = pending_migrations(files, applied)
        if not pendings:
            print("No pending migrations")
            return

        for file_path in pendings:
            ok, message = execute_migration(file_path)
            if not ok:
                raise RuntimeError(f"Failed: {file_path.name} -> {message}")
            print(f"Success: {file_path.name} ({message})")


if __name__ == "__main__":
    main()
