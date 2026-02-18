import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

class Database:
    def __init__(self, db_path='data/income_bot.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """Create tables if they don't exist."""
        cursor = self.conn.cursor()
        # Keywords table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'pending',
                added_date TEXT,
                assigned_date TEXT,
                completed_date TEXT,
                error TEXT
            )
        ''')
        # Articles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword_id INTEGER,
                filename TEXT NOT NULL,
                title TEXT,
                published_date TEXT,
                status TEXT DEFAULT 'draft',
                gemini_tokens INTEGER DEFAULT 0,
                affiliate_links INTEGER DEFAULT 0,
                FOREIGN KEY (keyword_id) REFERENCES keywords(id)
            )
        ''')
        # Publish log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS publish_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                published_at TEXT,
                github_commit TEXT,
                url TEXT,
                status TEXT DEFAULT 'success',
                error TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
        ''')
        # Metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                date TEXT PRIMARY KEY,
                articles_published INTEGER DEFAULT 0,
                api_calls INTEGER DEFAULT 0,
                tokens_used INTEGER DEFAULT 0,
                errors INTEGER DEFAULT 0,
                earnings_estimate REAL DEFAULT 0.0
            )
        ''')
        # Audit log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                module TEXT,
                action TEXT,
                details TEXT,
                level TEXT DEFAULT 'info'
            )
        ''')
        # Job queue for resilient processing
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_type TEXT NOT NULL,
                payload TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                result TEXT,
                error TEXT
            )
        ''')
        self.conn.commit()

    def log(self, module: str, action: str, details: str = "", level: str = "info"):
        """Write an audit log entry."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO audit_log (timestamp, module, action, details, level) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), module, action, details, level)
        )
        self.conn.commit()

    def add_keyword(self, keyword: str) -> int:
        """Insert a new keyword if not exists. Returns keyword ID."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO keywords (keyword, status, added_date) VALUES (?, ?, ?)",
                (keyword, 'pending', datetime.now().isoformat())
            )
            self.conn.commit()
            if cursor.lastrowid:
                return cursor.lastrowid
            # If already exists, fetch its ID
            cursor.execute("SELECT id FROM keywords WHERE keyword = ?", (keyword,))
            row = cursor.fetchone()
            return row['id'] if row else None
        except Exception as e:
            self.log('database', 'add_keyword', f'Error: {e}', 'error')
            raise

    def get_next_keywords(self, n: int) -> List[Dict[str, Any]]:
        """Get up to n pending keywords, mark them as assigned."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM keywords WHERE status = 'pending' ORDER BY added_date LIMIT ?",
            (n,)
        )
        rows = cursor.fetchall()
        keyword_ids = []
        for row in rows:
            kw_id = row['id']
            cursor.execute(
                "UPDATE keywords SET status = 'assigned', assigned_date = ? WHERE id = ?",
                (datetime.now().isoformat(), kw_id)
            )
            keyword_ids.append(kw_id)
        self.conn.commit()
        return [dict(row) for row in rows if row['id'] in keyword_ids]

    def mark_keyword_completed(self, keyword: str):
        """Mark keyword as completed."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE keywords SET status = 'completed', completed_date = ? WHERE keyword = ?",
            (datetime.now().isoformat(), keyword)
        )
        self.conn.commit()

    def get_keyword_by_text(self, keyword: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM keywords WHERE keyword = ?", (keyword,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def add_article(self, keyword_id: int, filename: str, title: str, tokens: int) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO articles (keyword_id, filename, title, published_date, status, gemini_tokens) VALUES (?, ?, ?, ?, ?, ?)",
            (keyword_id, filename, title, datetime.now().isoformat(), 'published', tokens)
        )
        self.conn.commit()
        return cursor.lastrowid

    def log_publish(self, article_id: int, commit_sha: str = None, url: str = None, status: str = 'success', error: str = None):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO publish_log (article_id, published_at, github_commit, url, status, error) VALUES (?, ?, ?, ?, ?, ?)",
            (article_id, datetime.now().isoformat(), commit_sha, url, status, error)
        )
        self.conn.commit()

    def increment_metric(self, date: str = None, **kwargs):
        """Update metrics for a given date (defaults to today)."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        cursor = self.conn.cursor()
        # Check if row exists
        cursor.execute("SELECT * FROM metrics WHERE date = ?", (date,))
        row = cursor.fetchone()
        if row:
            updates = []
            params = []
            for key, value in kwargs.items():
                updates.append(f"{key} = {key} + ?")
                params.append(value)
            params.append(date)
            cursor.execute(f"UPDATE metrics SET {', '.join(updates)} WHERE date = ?", params)
        else:
            # Insert new row
            cols = ['date'] + list(kwargs.keys())
            placeholders = ['?'] * (1 + len(kwargs))
            values = [date] + list(kwargs.values())
            cursor.execute(
                f"INSERT INTO metrics ({', '.join(cols)}) VALUES ({', '.join(placeholders)})",
                values
            )
        self.conn.commit()

    def get_recent_metrics(self, days: int = 7) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM metrics WHERE date >= date('now', ?) ORDER BY date",
            (f'-{days} days',)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def record_error(self):
        """Increment error count for today."""
        self.increment_metric(errors=1)

    def close(self):
        self.conn.close()

# Convenience wrapper functions
def get_or_create_keyword(db: Database, keyword: str) -> int:
    kw = db.get_keyword_by_text(keyword)
    if kw:
        return kw['id']
    return db.add_keyword(keyword)