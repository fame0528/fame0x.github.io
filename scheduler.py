#!/usr/bin/env python3
import os
import sys
import yaml
from datetime import datetime
from src.database import Database
from src.keyword_researcher import KeywordResearcher
from src.product_fetcher import ProductFetcher
from src.content_generator import ContentGenerator
from src.image_fetcher import ImageFetcher
from src.publisher import Publisher
from src.utils import slugify
from src.logger import StructuredLogger
from src.metrics import MetricsCollector
from src.cache import TTLCache
from src.parallel import parallel_map
from src.obsidian_logger import log_to_obsidian

def load_config(config_path='config.yaml'):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file {config_path} not found")
    with open(config_path) as f:
        return yaml.safe_load(f)

def _validate_article(content, filename, logger):
    """Check article meets quality standards before publishing."""
    issues = []
    if len(content) < 1000:
        issues.append(f"Article too short ({len(content)} chars)")
    if '[AMAZON_LINK' not in content:
        issues.append("Missing affiliate link placeholders")
    if content.count('```') % 2 != 0:
        issues.append("Unclosed code block")
    if issues:
        logger.warning('validation', 'Article validation issues', issues=issues)
        print(f"⚠️ Validation: {', '.join(issues)}")
    else:
        logger.info('validation', 'Article validated', filename=filename)

def _log_to_obsidian(config, entry):
    try:
        vault_path = config.get('obsidian_vault_path') or os.getenv('OBSIDIAN_VAULT_PATH')
        if vault_path:
            log_to_obsidian(vault_path=vault_path, entry=entry, category='IncomeBot')
    except Exception:
        pass

def _write_daily_report(metrics):
    """Write a simple daily report to disk."""
    report_dir = 'reports'
    os.makedirs(report_dir, exist_ok=True)
    date_str = datetime.now().strftime('%Y-%m-%d')
    report_file = os.path.join(report_dir, f'{date_str}.md')
    data = metrics.get_daily_metrics(1)
    with open(report_file, 'w') as f:
        f.write(f"# Income Bot Daily Report — {date_str}\n\n")
        f.write(f"- Articles today: {data['totals']['articles_published']}\n")
        f.write(f"- API calls: {data['totals']['api_calls']}\n")
        f.write(f"- Tokens used: {data['totals']['tokens_used']}\n")
        f.write(f"- Errors: {data['totals']['errors']}\n")

def main():
    start_time = datetime.now()
    config = load_config()
    db = Database()
    logger = StructuredLogger(config, db)
    metrics = MetricsCollector(db)
    cache = TTLCache(ttl_seconds=86400)

    logger.info('scheduler', 'Starting Income Bot run')

    try:
        kr = KeywordResearcher(config, db)
        pf = ProductFetcher(config, cache)
        cg = ContentGenerator(config, db)
        img = ImageFetcher(config)
        pub = Publisher(config, db)

        keywords = kr.get_next_keywords(1)
        if not keywords:
            logger.warning('scheduler', 'No pending keywords available')
            print("No pending keywords to process.")
            return

        keyword = keywords[0]
        logger.info('scheduler', f'Processing keyword: {keyword}')
        print(f"Processing: {keyword}")

        products = pf.fetch_products(keyword)
        if not products:
            logger.warning('scheduler', f'No products found for {keyword}')
            kr.mark_failed('No products found')
            return

        try:
            article_md = cg.generate_article(keyword, products)
        except Exception as e:
            logger.error('scheduler', 'Content generation failed', keyword=keyword, error=str(e))
            kr.mark_failed(str(e))
            return

        product_names = [p['name'] for p in products]
        image_urls = parallel_map(lambda name: img.fetch_image(name), product_names, max_workers=2)
        for p, img_url in zip(products, image_urls):
            placeholder = f'![{p["name"]}](image_url)'
            article_md = article_md.replace(placeholder, f'![{p["name"]}]({img_url})')
            link_placeholder = f'[AMAZON_LINK_{p["name"].upper().replace(" ", "_")}]'
            if p.get('url'):
                article_md = article_md.replace(link_placeholder, p['url'])

        filename = slugify(keyword) + '.md'
        _validate_article(article_md, filename, logger)

        try:
            commit_sha = pub.publish_article(filename, article_md, category=config['niche']['name'].lower().replace(' ', '-'))
        except Exception as e:
            logger.error('scheduler', 'Publish failed', keyword=keyword, error=str(e))
            kr.mark_failed(str(e))
            return

        kr.mark_completed(keyword)
        metrics.record_article_published(tokens_used=cg.last_tokens_used)
        logger.info('scheduler', 'Run completed successfully', keyword=keyword, commit=commit_sha, tokens=cg.last_tokens_used)
        print(f"✅ Completed: {filename}")
        _log_to_obsidian(config, f"Published {filename} for keyword '{keyword}'\nCommit: {commit_sha}")

    except Exception as e:
        logger.critical('scheduler', 'Unhandled exception in main loop', exception=str(e))
        print(f"❌ Critical error: {e}")
        raise
    finally:
        db.close()
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info('scheduler', f'Run finished in {elapsed:.2f}s')

    _write_daily_report(metrics)

if __name__ == '__main__':
    main()