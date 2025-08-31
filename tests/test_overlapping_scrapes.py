#!/usr/bin/env python3

import sys
sys.path.append('.')

from database_manager import DatabaseManager
import grpc
from src.scrapqt import services_pb2, services_pb2_grpc

def test_overlapping_scrapes():
    """Test duplicate detection with overlapping scraping queries"""
    print("=== Testing Overlapping Scrape Queries ===\n")
    
    # Initialize database manager
    db = DatabaseManager()
    
    # Check initial statistics
    print("1. Initial Database Statistics:")
    stats = db.get_duplicate_statistics()
    print(f"   Total products: {stats['total_products']}")
    print(f"   Unique URLs: {stats['unique_urls']}")
    print()
    
    # Test overlapping queries that should generate some duplicate products
    overlap_queries = [
        "gaming mouse",
        "wireless gaming mouse",  # Should have overlap with first query
        "mouse gaming",  # Should have overlap with both
    ]
    
    print("2. Running Overlapping Scraping Queries:")
    
    with grpc.insecure_channel('localhost:60002') as channel:
        scraper_stub = services_pb2_grpc.ScraperStub(channel)
        
        for i, query in enumerate(overlap_queries, 1):
            print(f"   Scraping {i}/{len(overlap_queries)}: '{query}'")
            try:
                response = scraper_stub.Scrape(services_pb2.ScrapeRequest(query=query))
                print(f"   ✓ Success: {response.items_scraped} items scraped")
            except grpc.RpcError as e:
                print(f"   ✗ Failed: {e.details()}")
    
    print()
    
    # Check updated statistics
    print("3. Updated Database Statistics:")
    new_stats = db.get_duplicate_statistics()
    print(f"   Total products: {new_stats['total_products']}")
    print(f"   Unique URLs: {new_stats['unique_urls']}")
    print(f"   Products added: {new_stats['total_products'] - stats['total_products']}")
    print(f"   New unique URLs: {new_stats['unique_urls'] - stats['unique_urls']}")
    
    # Calculate efficiency
    total_scraped = new_stats['total_products'] - stats['total_products']
    unique_added = new_stats['unique_urls'] - stats['unique_urls']
    if total_scraped > 0:
        efficiency = (unique_added / total_scraped) * 100
        duplicates_detected = total_scraped - unique_added
        print(f"   Duplicate detection efficiency: {efficiency:.1f}%")
        print(f"   Duplicates detected: {duplicates_detected}")
    print()
    
    # Test search functionality across queries
    print("4. Testing Cross-Query Search:")
    search_results = db.search_products("mouse")
    print(f"   Search for 'mouse': {len(search_results)} results")
    
    # Show products and their associated queries
    unique_urls = set()
    query_associations = {}
    
    for product in search_results:
        url_hash = product.get('url_hash', 'unknown')
        query_text = product.get('query_text', 'unknown')
        
        if url_hash not in query_associations:
            query_associations[url_hash] = {
                'title': product['title'],
                'price': product['price'],
                'queries': set()
            }
        
        query_associations[url_hash]['queries'].add(query_text)
        unique_urls.add(url_hash)
    
    print(f"   Unique products found: {len(unique_urls)}")
    print(f"   Products linked to multiple queries:")
    
    multi_query_count = 0
    for url_hash, data in query_associations.items():
        if len(data['queries']) > 1:
            multi_query_count += 1
            print(f"     - {data['title']} (${data['price']:.2f})")
            print(f"       Linked queries: {', '.join(sorted(data['queries']))}")
    
    print(f"   Products with multiple query links: {multi_query_count}/{len(unique_urls)}")

if __name__ == "__main__":
    test_overlapping_scrapes()
