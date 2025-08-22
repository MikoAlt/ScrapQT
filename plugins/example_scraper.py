import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scraper.base_scraper import BaseScraper

class ExampleScraper(BaseScraper):
    """
    An example scraper for a fictional e-commerce platform.
    """
    @property
    def ecommerce_name(self) -> str:
        return "ExampleCommerce"

    def scrape(self, query: str) -> list[dict]:
        """
        Simulates scraping data for the given query.
        """
        print(f"Scraping {self.ecommerce_name} for '{query}'...")
        # In a real implementation, this would involve making HTTP requests
        # and parsing HTML.
        return [
            {
                'title': f'{query} - Item 1',
                'price': 100.0,
                'review_score': 4.5,
                'review_count': 120,
                'link': f'http://example.com/product/1?query={query}',
                'is_used': False
            },
            {
                'title': f'{query} - Item 2',
                'price': 150.0,
                'review_score': 4.8,
                'review_count': 250,
                'link': f'http://example.com/product/2?query={query}',
                'is_used': True
            }
        ]
