#!/usr/bin/env python3

import sys
sys.path.append('.')

from database_manager import DatabaseManager
import grpc
from src.scrapqt import services_pb2, services_pb2_grpc

def test_duplicate_detection():
    """Test the URL hashing and duplicate detection system"""
    print("=== Testing URL Hashing and Duplicate Detection ===\n")
    
    # Initialize database manager
    db = DatabaseManager()
    
    # Check current duplicate statistics
    print("1. Current Database Statistics:")
    stats = db.get_duplicate_statistics()
    print(f"   Total products: {stats['total_products']}")
    print(f"   Unique URLs: {stats['unique_urls']}")
    print(f"   Duplicate groups: {stats['duplicate_groups']}")
    print(f"   Total duplicates: {stats['total_duplicates']}")
    print()
    
    # Test scraping the same query multiple times to create duplicates
    print("2. Testing Duplicate Prevention:")
    test_query = "wireless headphones"  # This should create overlapping products
    
    with grpc.insecure_channel('localhost:60002') as channel:
        scraper_stub = services_pb2_grpc.ScraperStub(channel)
        
        # Scrape the same query twice
        print(f"   First scrape for '{test_query}':")
        try:
            response1 = scraper_stub.Scrape(services_pb2.ScrapeRequest(query=test_query))
            print(f"   ✓ First scrape: {response1.items_scraped} items")
        except grpc.RpcError as e:
            print(f"   ✗ First scrape failed: {e.details()}")
            return
        
        print(f"   Second scrape for '{test_query}' (should detect duplicates):")
        try:
            response2 = scraper_stub.Scrape(services_pb2.ScrapeRequest(query=test_query))
            print(f"   ✓ Second scrape: {response2.items_scraped} items")
        except grpc.RpcError as e:
            print(f"   ✗ Second scrape failed: {e.details()}")
            return
    
    print()
    
    # Check updated statistics
    print("3. Updated Database Statistics:")
    new_stats = db.get_duplicate_statistics()
    print(f"   Total products: {new_stats['total_products']}")
    print(f"   Unique URLs: {new_stats['unique_urls']}")
    print(f"   Duplicate groups: {new_stats['duplicate_groups']}")
    print(f"   Total duplicates: {new_stats['total_duplicates']}")
    
    # Show the difference
    print(f"   Products added: {new_stats['total_products'] - stats['total_products']}")
    print(f"   New unique URLs: {new_stats['unique_urls'] - stats['unique_urls']}")
    print()
    
    # Test search to make sure products are still findable
    print("4. Testing Search Functionality:")
    search_results = db.search_products(test_query.split()[0])  # Search for "wireless"
    print(f"   Search for 'wireless': {len(search_results)} results")
    
    # Show sample results
    for i, product in enumerate(search_results[:3]):
        print(f"   {i+1}. {product['title']} - ${product['price']:.2f}")
        print(f"      Query: {product.get('query_text', 'N/A')}")
        print(f"      URL Hash: {product.get('url_hash', 'N/A')[:8]}...")
        print()

if __name__ == "__main__":
    test_duplicate_detection()
