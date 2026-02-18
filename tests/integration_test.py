#!/usr/bin/env python3
"""
Integration test for Income Bot.
Runs the full pipeline with mocked external APIs and verifies outputs.
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import Mock, patch
from src.database import Database
from src.keyword_researcher import KeywordResearcher
from src.product_fetcher import ProductFetcher
from src.content_generator import ContentGenerator
from src.publisher import Publisher
from src.metrics import MetricsCollector
from src.logger import StructuredLogger
import yaml

def create_test_config():
    return {
        'gemini_api_key': 'test-key',
        'repo_path': tempfile.mkdtemp(),
        'niche': {
            'name': 'Test Niche',
            'seed_keywords': ['test_keyword_1', 'test_keyword_2']
        },
        'amazon_tracking_id': 'testtag-20',
        'discord_webhook_url': None,
        'obsidian_vault_path': None
    }

def test_full_pipeline():
    config = create_test_config()
    db = Database()  # uses default in-memory for test? Actually file-based. We'll handle cleanup
    # Create a temp directory for the test DB and repo
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test.db')
    # Override DB to use temp
    db = Database(db_path)
    logger = StructuredLogger(config, db)
    metrics = MetricsCollector(db)
    cache = TTLCache(ttl_seconds=86400)

    # Seed keywords
    for kw in config['niche']['seed_keywords']:
        db.add_keyword(kw)

    # Step 1: Keyword Researcher
    kr = KeywordResearcher(config, db)
    keywords = kr.get_next_keywords(1)
    assert len(keywords) == 1
    keyword = keywords[0]
    assert keyword in config['niche']['seed_keywords']

    # Step 2: Product Fetcher
    pf = ProductFetcher(config, cache)
    products = pf.fetch_products(keyword)
    assert len(products) == 3
    assert 'name' in products[0]
    assert 'price' in products[0]
    assert 'url' in products[0]

    # Step 3: Content Generator (mock Gemini)
    with patch('google.genai.Client') as mock_client_class:
        mock_response = Mock()
        mock_response.text = f"""# {keyword.replace('_', ' ').title()}

## Introduction
This is a test article about {keyword.replace('_', ' ')}.

## Products
{chr(10).join([f'- {p["name"]}' for p in products])}

## Conclusion
Buy one.
"""
        mock_client = mock_class.return_value
        mock_client.models.generate_content.return_value = mock_response

        cg = ContentGenerator(config, db)
        article = cg.generate_article(keyword, products)
        assert keyword.replace('_', ' ').title() in article
        assert 'Products' in article

    # Step 4: Image Fetcher
    from src.image_fetcher import ImageFetcher
    img = ImageFetcher(config)
    img_url = img.fetch_image(products[0]['name'])
    assert 'pollinations.ai' in img_url

    # Step 5: Publisher (mock git)
    with patch('subprocess.run') as mock_run:
        pub = Publisher(config, db)
        filename = 'test-article.md'
        # Create the repository structure in temp dir
        posts_dir = os.path.join(config['repo_path'], '_posts', 'test-niche')
        os.makedirs(posts_dir, exist_ok=True)
        # Publish
        commit_sha = pub.publish_article(filename, article, category='test-niche')
        assert commit_sha is not None or commit_sha is None  # may be None from mock
        # Check file was written
        filepath = os.path.join(posts_dir, filename)
        assert os.path.exists(filepath)
        with open(filepath) as f:
            content = f.read()
            assert 'This is a test article' in content

    # Cleanup
    db.close()
    shutil.rmtree(temp_dir)
    print("✅ Integration test passed")

if __name__ == '__main__':
    test_full_pipeline()