import json
import os
from datetime import datetime
from .database import Database, get_or_create_keyword

class KeywordResearcher:
    def __init__(self, config, db: Database = None):
        self.config = config
        self.db = db or Database()
        self.cache_file = 'data/keywords_cache.json'
        self.keywords = self._load_keywords()

    def _load_keywords(self):
        # Load from database instead of file now
        # Seed keywords come from config on first run
        # Always ensure seed keywords are present
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM keywords")
        count = cursor.fetchone()[0]
        if count == 0:
            # Seed from config
            seed = self.config.get('niche', {}).get('seed_keywords', [])
            for kw in seed:
                self.db.add_keyword(kw)
        return []  # We'll query on demand

    def get_next_keywords(self, n):
        rows = self.db.get_next_keywords(n)
        self.keywords = [row['keyword'] for row in rows]
        return self.keywords

    def mark_completed(self, keyword: str):
        self.db.mark_keyword_completed(keyword)
        self.db.log('keyword_researcher', 'mark_completed', f'Keyword {keyword} completed')

    def mark_failed(self, keyword: str, error: str = None):
        kw_id = self.db.get_keyword_by_text(keyword)['id'] if self.db.get_keyword_by_text(keyword) else None
        if kw_id:
            cursor = self.db.conn.cursor()
            cursor.execute(
                "UPDATE keywords SET status = 'failed', error = ? WHERE id = ?",
                (error, kw_id)
            )
            self.db.conn.commit()
            self.db.log('keyword_researcher', 'mark_failed', f'Keyword {keyword} failed: {error}', level='error')