import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any
from threading import Lock

class JobQueue:
    def __init__(self, db: 'Database'):
        self.db = db
        self.lock = Lock()

    def enqueue(self, job_type: str, payload: Dict[str, Any]) -> int:
        """Add a job to the queue. Returns job ID."""
        with self.lock:
            cursor = self.db.conn.cursor()
            cursor.execute(
                "INSERT INTO job_queue (job_type, payload, status, created_at) VALUES (?, ?, ?, ?)",
                (job_type, json.dumps(payload), 'pending', datetime.now().isoformat())
            )
            self.db.conn.commit()
            return cursor.lastrowid

    def dequeue(self) -> Optional[Dict[str, Any]]:
        """Get next pending job and mark as in_progress."""
        with self.lock:
            cursor = self.db.conn.cursor()
            cursor.execute(
                "SELECT * FROM job_queue WHERE status = 'pending' ORDER BY created_at LIMIT 1"
            )
            row = cursor.fetchone()
            if not row:
                return None
            job_id = row['id']
            cursor.execute(
                "UPDATE job_queue SET status = 'in_progress', started_at = ? WHERE id = ?",
                (datetime.now().isoformat(), job_id)
            )
            self.db.conn.commit()
            return dict(row)

    def complete(self, job_id: int, result: Dict[str, Any] = None, error: str = None):
        """Mark job as complete (or failed)."""
        with self.lock:
            cursor = self.db.conn.cursor()
            if error:
                cursor.execute(
                    "UPDATE job_queue SET status = 'failed', error = ?, completed_at = ? WHERE id = ?",
                    (error, datetime.now().isoformat(), job_id)
                )
            else:
                cursor.execute(
                    "UPDATE job_queue SET status = 'completed', result = ?, completed_at = ? WHERE id = ?",
                    (json.dumps(result) if result else None, datetime.now().isoformat(), job_id)
                )
            self.db.conn.commit()

    def get_pending_count(self) -> int:
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM job_queue WHERE status = 'pending'")
        return cursor.fetchone()[0]

    def reset_stale_jobs(self, timeout_minutes: int = 30):
        """Reset jobs that have been in_progress for too long (crash recovery)."""
        with self.lock:
            cursor = self.db.conn.cursor()
            cutoff = datetime.now().timestamp() - (timeout_minutes * 60)
            cursor.execute(
                "UPDATE job_queue SET status = 'pending' WHERE status = 'in_progress' AND started_at < ?",
                (datetime.fromtimestamp(cutoff).isoformat(),)
            )
            self.db.conn.commit()