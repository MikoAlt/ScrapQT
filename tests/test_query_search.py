#!/usr/bin/env python3

from database_manager import DatabaseManager

def test_query_search():
    """Test the new query-based search functionality"""
    db = DatabaseManager()
    
    # Test different search terms
    test_searches = ["gaming", "keyboard", "mouse", "wireless", "smartphone"]
    
    for search_term in test_searches:
        print(f"\n=== Searching for: '{search_term}' ===")
        results = db.search_products(search_term)
        print(f"Found {len(results)} products")
        
        for product in results[:3]:  # Show first 3 results
            print(f"  • {product['title']}")
            print(f"    Query: {product['query_text']}")
            print(f"    Price: ${product['price']:.2f}")
            print()

if __name__ == "__main__":
    test_query_search()
