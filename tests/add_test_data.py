#!/usr/bin/env python3

import grpc
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.scrapqt import services_pb2, services_pb2_grpc

def add_test_queries():
    """Add some test queries to demonstrate fuzzy search"""
    test_queries = [
        "wireless mouse",
        "smartphone",  
        "laptop gaming",
        "mechanical keyboard"
    ]
    
    print("Adding test queries for fuzzy search demonstration...")
    
    with grpc.insecure_channel('localhost:60002') as channel:
        scraper_stub = services_pb2_grpc.ScraperStub(channel)
        
        for query in test_queries:
            try:
                print(f"Scraping: {query}")
                response = scraper_stub.Scrape(services_pb2.ScrapeRequest(query=query))
                print(f"✓ Success: {response.items_scraped} items scraped")
            except grpc.RpcError as e:
                print(f"✗ Error: {e.details()}")
        
        print("\nDone! Now you can test fuzzy search with more diverse queries.")

if __name__ == "__main__":
    add_test_queries()
