#!/usr/bin/env python3
"""
Income Bot CLI - Entry point for running the automation.

Modes:
  --once         Generate and publish one article (default)
  --daemon       Run continuously with schedule (not implemented in prototype)
  --health       Run health check and exit
  --test         Run integration test with mock data
  --setup        First-time setup: create DB, seed keywords, etc.
"""

import argparse
import sys
import os
from datetime import datetime
from src.database import Database
from src.logger import StructuredLogger
from src.metrics import MetricsCollector
from src.circuit_breaker import CircuitBreaker
from src.retry_handler import retry, RetryConfig
from src.job_queue import JobQueue
from src.cache import TTLCache
from src.parallel import parallel_map
from src.security import ConfigSecurity
from scheduler import load_config, ContentGenerator, Publisher, KeywordResearcher, ProductFetcher, ImageFetcher

def run_once(config, db, logger, metrics):
    """Generate and publish one article."""
    logger.info('run_once', 'Starting single article generation')
    try:
        kr = KeywordResearcher(config, db)
        pf = ProductFetcher(config)
        cg = ContentGenerator(config)
        img = ImageFetcher(config)
        pub = Publisher(config, db)

        keywords = kr.get_next_keywords(1)
        if not keywords:
            logger.warning('run_once', 'No pending keywords')
            print("No pending keywords to process.")
            return

        keyword = keywords[0]
        logger.info('run_once', f'Processing keyword: {keyword}')
        print(f"Processing: {keyword}")

        products = pf.fetch_products(keyword)
        if not products:
            logger.warning('run_once', f'No products for {keyword}, skipping')
            kr.mark_keyword_failed(keyword)
            return

        article_md = cg.generate_article(keyword, products)
        # Fetch images (parallel for each product)
        product_names = [p['name'] for p in products]
        image_urls = parallel_map(lambda name: img.fetch_image(name), product_names, max_workers=2)
        for p, img_url in zip(products, image_urls):
            placeholder = f'![{p["name"]}](image_url)'
            article_md = article_md.replace(placeholder, f'![{p["name"]}]({img_url})')
            link_placeholder = f'[AMAZON_LINK_{p["name"].upper().replace(" ", "_")}]'
            if p.get('url'):
                article_md = article_md.replace(link_placeholder, p['url'])

        filename = keyword.lower().replace(' ', '-') + '.md'
        commit_sha = pub.publish_article(filename, article_md, category='pet-care')
        metrics.record_article_published(tokens_used=cg.last_tokens_used)
        logger.info('run_once', f'Published article: {filename}', commit=commit_sha)
        print(f"[OK] Published: {filename}")
    except Exception as e:
        import traceback
        logger.error('run_once', 'Failed', exception=traceback.format_exc())
        metrics.record_error()
        print(f"[ERROR] Error: {e}")
        print(traceback.format_exc())
        raise

def run_health_check(config, db, logger):
    """Run health checks and output status."""
    from health_check import run_health_check as hc
    results = hc()
    print("\n=== HEALTH CHECK ===")
    for r in results:
        symbol = "[OK]" if r['status'] == 'GREEN' else "[WARN]" if r['status'] == 'YELLOW' else "[ERROR]"
        print(f"{symbol} {r['name']}: {r['details']}")
    logger.info('health_check', 'Health check completed', results=results)
    return results

def run_test(config, db, logger):
    """Run integration test with mocked APIs."""
    print("Running integration test...")
    # Simple test: generate article with mock Gemini
    try:
        cg = ContentGenerator(config)
        test_keyword = "test_supplements_for_dogs"
        mock_products = [{'name': 'Test Product', 'price': 29.99, 'rating': 4.5, 'url': 'https://example.com'}]
        article = cg.generate_article(test_keyword, mock_products)
        assert "Test Product" in article
        print("[OK] Integration test passed")
        logger.info('test', 'Integration test passed')
        return True
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        logger.error('test', 'Integration test failed', error=str(e))
        return False

def setup_database(config, db, logger):
    """First-time setup: create tables, seed initial keywords."""
    logger.info('setup', 'Initializing database and seeding keywords')
    seed_keywords = config.get('niche', {}).get('seed_keywords', [])
    count = 0
    for kw in seed_keywords:
        db.add_keyword(kw)
        count += 1
    logger.info('setup', f'Seeded {count} keywords')
    print(f"[OK] Database initialized with {count} seed keywords")

def main():
    parser = argparse.ArgumentParser(description='Income Bot Automation')
    parser.add_argument('--once', action='store_true', default=True, help='Generate one article (default)')
    parser.add_argument('--daemon', action='store_true', help='Run continuously (future)')
    parser.add_argument('--health', action='store_true', help='Run health check')
    parser.add_argument('--test', action='store_true', help='Run integration test')
    parser.add_argument('--setup', action='store_true', help='First-time setup')
    args = parser.parse_args()

    # Load config
    try:
        config = load_config()
    except Exception as e:
        print(f"❌ Failed to load config.yaml: {e}")
        sys.exit(1)

    # Initialize components
    db = Database()
    logger = StructuredLogger(config, db)
    metrics = MetricsCollector(db)
    ConfigSecurity.enforce_file_permissions('config.yaml')

    try:
        if args.setup:
            setup_database(config, db, logger)
        elif args.health:
            run_health_check(config, db, logger)
        elif args.test:
            success = run_test(config, db, logger)
            sys.exit(0 if success else 1)
        else:
            # Default: run once
            run_once(config, db, logger, metrics)
    except KeyboardInterrupt:
        logger.warning('main', 'Interrupted by user')
        print("\n[STOP] Stopped")
        sys.exit(0)
    except Exception as e:
        logger.critical('main', f'Unhandled exception: {e}', exception=str(e))
        print(f"[ERROR] Critical error: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == '__main__':
    main()