class ImageFetcher:
    def __init__(self, config):
        self.config = config

    def fetch_image(self, product_name):
        # Use pollinations.ai free text-to-image endpoint
        query = product_name.replace(' ', '+')
        url = f"https://image.pollinations.ai/prompt/{query}?width=800&height=600&noStore=true"
        return url