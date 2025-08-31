#!/usr/bin/env python3

from database_manager import DatabaseManager

def test_missing_queries():
    """Test queries that don't exist in the database to verify scraping prompt"""
    db = DatabaseManager()
    
    # Test with queries that likely don't exist
    test_queries = ["tablet", "webcam", "monitor 4K", "graphics card", "SSD drive"]
    
    print("=== Testing Queries Not in Database ===\n")
    
    for query in test_queries:
        results = db.search_products(query)
        print(f"Query: '{query}' -> {len(results)} results")
        if len(results) == 0:
            print(f"  ✓ '{query}' should trigger scraping prompt")
        else:
            print(f"  - '{query}' already has results")
        print()
    
    # Show all existing queries for reference
    print("=== All Existing Queries in Database ===")
    import sqlite3
    conn = sqlite3.connect('data/scraped_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT query_text FROM queries ORDER BY query_text')
    queries = cursor.fetchall()
    conn.close()
    
    for i, (query,) in enumerate(queries, 1):
        print(f"{i:2d}. {query}")

if __name__ == "__main__":
    test_missing_queries()
