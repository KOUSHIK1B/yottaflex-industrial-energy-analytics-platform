"""
Database Manager for YottaFlex Energy Analytics Platform
========================================================
Handles SQLite connection, schema creation, bulk insertions, and query execution.
Enforces foreign key constraints and transactional integrity.
Ensures zero resource leaks and Windows-safe file unlocking.
"""

import sqlite3
import gc
import time
import json
from pathlib import Path
from contextlib import contextmanager
from typing import List, Dict, Any, Tuple, Optional, Generator
import config

class DatabaseManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path or config.DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager that yields a configured SQLite connection
        and GUARANTEES it is committed and closed upon block exit.
        """
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_connection(self) -> sqlite3.Connection:
        """
        Returns an open connection.
        Caller is responsible for calling conn.close().
        """
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            return conn
        except BaseException:
            conn.close()
            raise

    def close(self) -> None:
        """Triggers garbage collection to release any lingering connection handles."""
        gc.collect()

    def checkpoint_and_close(self) -> None:
        """Checkpoints WAL and truncates WAL/SHM files to release locks safely."""
        gc.collect()
        if self.db_path.exists():
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            try:
                conn.execute("PRAGMA busy_timeout = 30000;")
                checkpoint = conn.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
                if checkpoint is None or checkpoint[0] != 0:
                    raise sqlite3.OperationalError("SQLite WAL checkpoint could not complete.")
            finally:
                conn.close()
        gc.collect()

    def remove_database(self) -> bool:
        """
        Safely removes the database and any companion WAL/SHM files.
        Handles Windows file locks by checkpointing, garbage collecting, and retrying.
        """
        self.checkpoint_and_close()
        
        files_to_remove = [
            Path(f"{self.db_path}-wal"),
            Path(f"{self.db_path}-shm"),
            self.db_path,
        ]
        
        success = True
        for f in files_to_remove:
            if f.exists():
                removed = False
                for attempt in range(3):
                    try:
                        f.unlink()
                        removed = True
                        break
                    except (PermissionError, OSError):
                        time.sleep(0.05 * (attempt + 1))
                        gc.collect()
                if not removed:
                    success = False
        return success

    def initialize_schema(self, schema_path: Optional[Path] = None) -> None:
        """Initializes database schema from SQL file."""
        schema_file = Path(schema_path or (config.SQL_DIR / "schema.sql"))
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found at {schema_file}")
            
        with open(schema_file, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        with self.connection() as conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.executescript(schema_sql)

    def bulk_insert(self, table_name: str, records: List[Dict[str, Any]]) -> int:
        """Efficiently inserts multiple dictionaries into a table."""
        if not records:
            return 0
            
        columns = list(records[0].keys())
        placeholders = ", ".join(["?"] * len(columns))
        col_names = ", ".join(columns)
        sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
        
        data_tuples = [[rec.get(c) for c in columns] for rec in records]
        
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, data_tuples)
            return cursor.rowcount

    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Executes a SQL query and returns results as list of dicts."""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def ensure_schema(self) -> None:
        """Ensures that the schema is created if no tables exist in the database."""
        with self.connection() as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';").fetchone()[0]
        if cnt == 0:
            self.initialize_schema()

    def verify_integrity(self) -> Dict[str, Any]:
        """Runs SQLite integrity and foreign key checks."""
        with self.connection() as conn:
            integrity = conn.execute("PRAGMA integrity_check;").fetchall()
            foreign_keys = conn.execute("PRAGMA foreign_key_check;").fetchall()
            
            return {
                "integrity_check": [dict(r) for r in integrity],
                "foreign_key_violations": [dict(r) for r in foreign_keys],
                "is_valid": len(integrity) == 1 and integrity[0][0] == "ok" and len(foreign_keys) == 0
            }

    def generate_integrity_report(self) -> Dict[str, Any]:
        """
        Gathers comprehensive SQLite database integrity statistics and table counts,
        and saves the report to outputs/database_integrity_report.json.
        """
        tables = [
            "plants", "meters", "machines", "machine_meter_assignments",
            "shifts", "tariffs", "weather_observations", "production_batches",
            "energy_readings", "maintenance_events", "machine_idle_periods",
            "recommendations", "anomaly_ground_truth"
        ]
        with self.connection() as conn:
            integrity = conn.execute("PRAGMA integrity_check;").fetchall()
            foreign_keys = conn.execute("PRAGMA foreign_key_check;").fetchall()
            journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
            fk_enforced = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
            
            table_counts = {}
            for tbl in tables:
                c = conn.execute(f"SELECT COUNT(*) FROM {tbl};").fetchone()[0]
                table_counts[tbl] = c

        db_size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0
        db_size_mb = round(db_size_bytes / (1024 * 1024), 2)
        is_valid = len(integrity) == 1 and integrity[0][0] == "ok" and len(foreign_keys) == 0

        report = {
            "database_file": str(self.db_path.name),
            "file_size_bytes": db_size_bytes,
            "file_size_mb": db_size_mb,
            "integrity_check_result": integrity[0][0] if integrity else "error",
            "foreign_key_violations_count": len(foreign_keys),
            "foreign_keys_enforced": bool(fk_enforced),
            "journal_mode": journal_mode,
            "table_record_counts": table_counts,
            "is_valid": is_valid,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        for out_dir in [config.OUTPUTS_DIR, config.ROOT_OUTPUTS_DIR]:
            out_dir.mkdir(parents=True, exist_ok=True)
            report_path = out_dir / "database_integrity_report.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

        return report
