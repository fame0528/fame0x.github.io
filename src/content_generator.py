import os
from datetime import datetime
import google.genai as genai
import yaml
from .retry_handler import retry, RetryConfig
from .circuit_breaker import CircuitBreaker
from .database import get_or_create_keyword

class ContentGenerator:
    def __init__(self, config, db: 'Database' = None):
        self.config = config
        api_key = config.get('gemini_api_key') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("Gemini API key not provided in config or environment")
        self.client = genai.Client(api_key=api_key)
        self.db = db
        self.circuit_breaker = CircuitBreaker('gemini_api', failure_threshold=5, recovery_timeout=120)
        self.last_tokens_used = 0

    @retry(exceptions=(Exception,), config=RetryConfig(max_attempts=3, base_delay=2))
    def generate_article(self, keyword, products):
        prompt = self._build_prompt(keyword, products)
        try:
            response = self.circuit_breaker.call(
                lambda: self.client.models.generate_content(
                    model='gemma-3-4b-it',
                    contents=prompt
                )
            )
            article_md = response.text
            # Estimate token usage (roughly 4 chars per token)
            self.last_tokens_used = len(prompt) + len(article_md) // 4
            if self.db:
                kw_id = get_or_create_keyword(self.db, keyword)
                self.db.increment_metric(api_calls=1, tokens_used=self.last_tokens_used)
        except Exception as e:
            article_md = self._generate_stub(keyword, products, error=str(e))
            self.last_tokens_used = 0
            if self.db:
                self.db.record_error()
                self.db.log('content_generator', 'generate_article_failed', f'Keyword: {keyword}, Error: {e}', level='error')
        return self._add_front_matter(keyword, article_md)

    def _build_prompt(self, keyword, products):
        products_text = "\n".join([f"- {p['name']}: ${p['price']:.2f}, rating {p['rating']}/5" for p in products])
        return f"""You are an experienced pet care specialist writing a comprehensive, honest review for dog owners.

Write a 2000-word article comparing these products for {keyword.replace('_', ' ')}.

Products to compare:
{products_text}

Structure:
1. Introduction (hook with anecdote)
2. Why this need matters for dog owners
3. Detailed comparison table (markdown)
4. In-depth review of each product with pros and cons
5. Testing methodology (simulate hands-on testing)
6. Frequently asked questions (FAQ)
7. Conclusion with recommendation and call-to-action

Tone: Warm, trustworthy, E-E-A-T compliant. Include personal experience simulation.
Keyword: {keyword}. For each product, include an affiliate link placeholder: [AMAZON_LINK_PRODUCT_NAME] where PRODUCT_NAME is the product name with spaces replaced by underscores.

Use Markdown formatting. Include image placeholders like `![product name](image_url)` for each product.

Word count: approximately 2000 words.
"""

    def _add_front_matter(self, keyword, content):
        date_str = datetime.now().strftime('%Y-%m-%d')
        title = keyword.replace('_', ' ').title()
        slug = keyword.lower().replace(' ', '-')
        front_matter = f"""---
title: "{title}"
date: {date_str}
slug: "{slug}"
categories: ["pet care", "dog health"]
tags: {[kw.lower() for kw in keyword.split('_')]}
---
"""
        return front_matter + content

    def _generate_stub(self, keyword, products, error):
        products_list = "\n".join([f"- {p['name']} (${p['price']:.2f})" for p in products])
        return f"""# {keyword.replace('_', ' ').title()}

*Note: This is a placeholder article generated due to API error: {error}*

## Introduction
We understand you're looking for the best {keyword.replace('_', ' ')}. This page is under construction.

## Top Products
{products_list}

## Why This Matters
[To be written...]

## Comparison Table
| Product | Price | Rating |
|---------|-------|--------|
{chr(10).join([f'| {p["name"]} | ${p["price"]:.2f} | {p["rating"]}/5 |' for p in products])}

## Conclusion
Check back soon for a full review.
"""