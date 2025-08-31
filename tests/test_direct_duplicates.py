#!/usr/bin/env python3

import sys
sys.path.append('.')
import sqlite3

from database_manager import DatabaseManager
import grpc
from src.scrapqt import services_pb2, services_pb2_grpc

def test_direct_duplicate_insertion():
    """Test duplicate detection by directly inserting duplicate items"""
    print("=== Testing Direct Duplicate Detection ===\n")
    
    # Initialize database manager
    db = DatabaseManager()
    
    # First, create a test query to get query_id
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO queries (query_text) VALUES (?)", ("test duplicate detection",))
    conn.commit()
    cursor.execute("SELECT id FROM queries WHERE query_text = ?", ("test duplicate detection",))
    query_id = cursor.fetchone()[0]
    conn.close()
    print(f"Using query ID: {query_id}")
    
    # Create test items with identical URLs using ScrapedItem
    def create_test_items():
        items = []
        
        # First item
        item1 = services_pb2.ScrapedItem()
        item1.title = "Test Product 1"
        item1.price = 99.99
        item1.link = "https://test.com/product/123"
        item1.image_url = "https://test.com/image1.jpg"
        item1.description = "First version of test product"
        item1.query_id = query_id
        item1.ecommerce = "test.com"
        item1.review_score = 4.5
        item1.review_count = 100
        item1.is_used = False
        item1.sentiment_score = 8
        items.append(item1)
        
        # Duplicate item (same URL)
        item2 = services_pb2.ScrapedItem()
        item2.title = "Test Product 1 (Duplicate)"
        item2.price = 89.99
        item2.link = "https://test.com/product/123"  # Same URL - should be detected as duplicate
        item2.image_url = "https://test.com/image1.jpg"
        item2.description = "Second version of same product"
        item2.query_id = query_id
        item2.ecommerce = "test.com"
        item2.review_score = 4.2
        item2.review_count = 85
        item2.is_used = False
        item2.sentiment_score = 7
        items.append(item2)
        
        # Different item (different URL)
        item3 = services_pb2.ScrapedItem()
        item3.title = "Test Product 2"
        item3.price = 149.99
        item3.link = "https://test.com/product/456"  # Different URL - should be saved
        item3.image_url = "https://test.com/image2.jpg"
        item3.description = "Different product"
        item3.query_id = query_id
        item3.ecommerce = "test.com"
        item3.review_score = 4.8
        item3.review_count = 200
        item3.is_used = False
        item3.sentiment_score = 9
        items.append(item3)
        
        return items
    
    # Check current statistics
    print("1. Current Database Statistics:")
    stats = db.get_duplicate_statistics()
    print(f"   Total products: {stats['total_products']}")
    print(f"   Unique URLs: {stats['unique_urls']}")
    print()
    
    # Test direct insertion via gRPC stream
    print("2. Testing Duplicate Detection via gRPC Stream:")
    
    with grpc.insecure_channel('localhost:60001') as channel:
        sentiment_stub = services_pb2_grpc.SentimentStub(channel)
        
        # Insert first batch (3 items, 2 with same URL)
        print("   Inserting first batch (3 items, 2 with same URL):")
        try:
            test_items = create_test_items()
            response = sentiment_stub.SaveItems(iter(test_items))
            print(f"   ✓ Response: success={response.success}, items_saved={response.items_saved}")
        except grpc.RpcError as e:
            print(f"   ✗ Save failed: {e.details()}")
            return
        
        # Create a second query for the same items
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO queries (query_text) VALUES (?)", ("test duplicate detection again",))
        conn.commit()
        cursor.execute("SELECT id FROM queries WHERE query_text = ?", ("test duplicate detection again",))
        query_id2 = cursor.fetchone()[0]
        conn.close()
        
        # Update items to use the new query_id
        test_items2 = create_test_items()
        for item in test_items2:
            item.query_id = query_id2
        
        # Try to insert the same items again - should all be duplicates
        print("   Inserting same URLs with different query (should detect duplicates):")
        try:
            response2 = sentiment_stub.SaveItems(iter(test_items2))
            print(f"   ✓ Response: success={response2.success}, items_saved={response2.items_saved}")
        except grpc.RpcError as e:
            print(f"   ✗ Second save failed: {e.details()}")
            return
    
    print()
    
    # Check updated statistics
    print("3. Updated Database Statistics:")
    new_stats = db.get_duplicate_statistics()
    print(f"   Total products: {new_stats['total_products']}")
    print(f"   Unique URLs: {new_stats['unique_urls']}")
    print(f"   Products added: {new_stats['total_products'] - stats['total_products']}")
    print()
    
    # Check how many queries link to the duplicated URL
    print("4. Checking Product-Query Linkages:")
    
    # Find the test URL hash
    test_url_hash = db._generate_url_hash("https://test.com/product/123")
    print(f"   Test URL hash: {test_url_hash}")
    
    # Check how many queries are linked to this product
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT q.query_text, p.title, p.price, p.url_hash
        FROM queries q
        JOIN product_queries pq ON q.id = pq.query_id
        JOIN products p ON pq.product_id = p.id
        WHERE p.url_hash = ?
    """, (test_url_hash,))
    
    links = cursor.fetchall()
    conn.close()
    print(f"   Found {len(links)} query-product links for the duplicate URL:")
    
    for query_text, title, price, url_hash in links:
        print(f"     - Query: '{query_text}' → {title} (${price:.2f})")

if __name__ == "__main__":
    test_direct_duplicate_insertion()
