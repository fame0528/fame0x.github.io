from .cache import TTLCache

class ProductFetcher:
    def __init__(self, config, cache: TTLCache = None):
        self.config = config
        self.amazon_tracking_id = config.get('amazon_tracking_id')
        self.cache = cache or TTLCache(ttl_seconds=86400)  # cache 24h

    def fetch_products(self, keyword):
        # Check cache first
        cached = self.cache.get(keyword)
        if cached:
            return cached
        # Generate plausible mock products (in real impl, would call Amazon PA-API or scrape)
        base = keyword.replace('_', ' ')
        products = [
            {
                'name': f"Best {base} - Premium Choice",
                'price': 49.99,
                'rating': 4.7,
                'asin': f"B{abs(hash(keyword)) % 10000000000}",
                'url': self._build_amazon_url(f"B{abs(hash(keyword)) % 10000000000}")
            },
            {
                'name': f"{base} Pro Kit",
                'price': 79.99,
                'rating': 4.5,
                'asin': f"B{abs(hash(keyword)+1) % 10000000000}",
                'url': self._build_amazon_url(f"B{abs(hash(keyword)+1) % 10000000000}")
            },
            {
                'name': f"Value {base}",
                'price': 29.99,
                'rating': 4.3,
                'asin': f"B{abs(hash(keyword)+2) % 10000000000}",
                'url': self._build_amazon_url(f"B{abs(hash(keyword)+2) % 10000000000}")
            }
        ]
        self.cache.set(keyword, products)
        return products

    def _build_amazon_url(self, asin):
        if self.amazon_tracking_id:
            return f"https://www.amazon.com/dp/{asin}?tag={self.amazon_tracking_id}"
        return f"https://www.amazon.com/dp/{asin}"