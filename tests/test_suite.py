import pytest
import os
import sys
import tempfile
import shutil

# Add parent dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import Database
from src.cache import TTLCache
from src.parallel import parallel_map

def test_database_connection():
    """Test that we can create a DB and tables."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    try:
        db = Database(db_path)
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert 'keywords' in tables
        assert 'articles' in tables
        assert 'publish_log' in tables
        assert 'metrics' in tables
        assert 'audit_log' in tables
        assert 'job_queue' in tables
        db.close()
    finally:
        os.unlink(db_path)

def test_add_and_get_keyword():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    try:
        db = Database(db_path)
        kw_id = db.add_keyword('test_keyword')
        assert kw_id is not None
        fetched = db.get_keyword_by_text('test_keyword')
        assert fetched['id'] == kw_id
        assert fetched['keyword'] == 'test_keyword'
        db.close()
    finally:
        os.unlink(db_path)

def test_metrics_increment():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    try:
        db = Database(db_path)
        db.increment_metric(articles_published=1, tokens_used=500)
        metrics = db.get_recent_metrics(1)
        assert len(metrics) == 1
        assert metrics[0]['articles_published'] == 1
        assert metrics[0]['tokens_used'] == 500
        db.close()
    finally:
        os.unlink(db_path)

def test_ttl_cache():
    cache = TTLCache(ttl_seconds=1)
    cache.set('key', 'value')
    assert cache.get('key') == 'value'
    import time; time.sleep(1.1)
    assert cache.get('key') is None

def test_parallel_map():
    def square(x): return x * x
    results = parallel_map(square, [1, 2, 3, 4], max_workers=2)
    assert results == [1, 4, 9, 16]

if __name__ == '__main__':
    pytest.main([__file__, '-v'])