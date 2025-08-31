#!/usr/bin/env python3
"""
Test script for the enhanced scrapers
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Test the enhanced scrapers
from src.scraper.plugins.example_scraper import ExampleScraper
from src.scraper.plugins.premium_scraper import PremiumScraper

def test_scrapers():
    print("=== Testing Enhanced Scrapers ===\n")
    
    # Test queries
    test_queries = ["gaming laptop", "wireless mouse", "smartphone"]
    
    # Initialize scrapers
    example_scraper = ExampleScraper()
    premium_scraper = PremiumScraper()
    
    for query in test_queries:
        print(f"Testing query: '{query}'")
        print("-" * 50)
        
        # Test Example Scraper
        print(f"\n{example_scraper.ecommerce_name} Results:")
        example_results = example_scraper.scrape(query)
        for i, product in enumerate(example_results[:2], 1):  # Show first 2 products
            print(f"  {i}. {product['title']}")
            print(f"     Price: ${product['price']:.2f}")
            print(f"     Rating: {product['review_score']}/5 ({product['review_count']} reviews)")
            print(f"     Description: {product['description'][:80]}...")
            print(f"     Used: {'Yes' if product['is_used'] else 'No'}")
            print()
        
        # Test Premium Scraper
        print(f"{premium_scraper.ecommerce_name} Results:")
        premium_results = premium_scraper.scrape(query)
        for i, product in enumerate(premium_results[:2], 1):  # Show first 2 products
            print(f"  {i}. {product['title']}")
            print(f"     Price: ${product['price']:.2f}")
            print(f"     Rating: {product['review_score']}/5 ({product['review_count']} reviews)")
            print(f"     Description: {product['description'][:80]}...")
            print(f"     Used: {'Yes' if product['is_used'] else 'No'}")
            print()
        
        print("=" * 70)
        print()

if __name__ == "__main__":
    test_scrapers()
