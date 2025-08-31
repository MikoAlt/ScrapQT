#!/usr/bin/env python3

import grpc
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scrapqt import services_pb2, services_pb2_grpc

def test_scraper_service():
    """Test the scraper service with enhanced data"""
    print("=== Testing Enhanced Scraper Service ===\n")
    
    test_queries = ["gaming laptop", "wireless mouse", "smartphone"]
    
    with grpc.insecure_channel('localhost:60002') as channel:
        scraper_stub = services_pb2_grpc.ScraperStub(channel)
        
        for query in test_queries:
            print(f"Scraping for: '{query}'")
            try:
                response = scraper_stub.Scrape(services_pb2.ScrapeRequest(query=query))
                print(f"✓ Success: {response.items_scraped} items scraped")
            except grpc.RpcError as e:
                print(f"✗ Error: {e.details()}")
            print()

if __name__ == "__main__":
    test_scraper_service()
