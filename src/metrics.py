from datetime import datetime
from typing import Dict, Any
from .database import Database

class MetricsCollector:
    def __init__(self, db: Database):
        self.db = db

    def increment(self, **counters: int):
        """Increment daily metrics counters."""
        self.db.increment_metric(**counters)

    def record_article_published(self, tokens_used: int):
        self.increment(articles_published=1, tokens_used=tokens_used, api_calls=1)

    def record_error(self):
        self.increment(errors=1)

    def get_daily_metrics(self, days: int = 7) -> Dict[str, Any]:
        rows = self.db.get_recent_metrics(days)
        return {
            'period_days': days,
            'daily': rows,
            'totals': {
                'articles_published': sum(r.get('articles_published', 0) for r in rows),
                'api_calls': sum(r.get('api_calls', 0) for r in rows),
                'tokens_used': sum(r.get('tokens_used', 0) for r in rows),
                'errors': sum(r.get('errors', 0) for r in rows),
            }
        }

    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate data for health dashboard."""
        metrics = self.get_daily_metrics(14)
        # Add system status
        return {
            'generated_at': datetime.now().isoformat(),
            'metrics': metrics,
            'status': 'HEALTHY' if metrics['totals']['errors'] == 0 else 'DEGRADED'
        }