#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from database_manager import DatabaseManager
from src.scraper.plugin_loader import load_plugins, generate_scraped_items

def test_enhanced_scrapers_direct():
    """Test enhanced scrapers directly with database integration"""
    print("=== Testing Enhanced Scrapers with Direct Database Integration ===\n")
    
    # Clear database
    db = DatabaseManager()
    db.clear_all_data()
    print("Database cleared")
    
    # Load plugins
    plugins = load_plugins('src/scraper/plugins')
    print(f"Loaded {len(plugins)} plugins: {[p.ecommerce_name for p in plugins]}")
    
    # Test queries
    test_queries = ["gaming laptop", "wireless mouse"]
    
    for query in test_queries:
        print(f"\n--- Testing query: '{query}' ---")
        
        # Add query to database
        query_id = db.add_query(query)
        print(f"Query added with ID: {query_id}")
        
        # Generate scraped items
        items = list(generate_scraped_items(plugins, query, query_id))
        print(f"Generated {len(items)} items")
        
        # Manually save items to database
        for item in items:
            product_data = {
                'title': item.title,
                'price': item.price,
                'review_score': item.review_score,
                'review_count': item.review_count,
                'link': item.link,
                'ecommerce': item.ecommerce,
                'is_used': item.is_used,
                'description': item.description,
                'query_id': item.query_id,
                'image_url': item.image_url
            }
            db.add_product(**product_data)
            print(f"  ✓ {product_data['title']} - ${product_data['price']:.2f}")
    
    # Show final database state
    print(f"\n--- Final Database State ---")
    all_products = db.get_all_products()
    print(f"Total products in database: {len(all_products)}")
    
    for product in all_products:
        print(f"• {product['title']} - ${product['price']:.2f} ({product['ecommerce']})")
        print(f"  Description: {product['description'][:60]}...")
        print()

if __name__ == "__main__":
    test_enhanced_scrapers_direct()
