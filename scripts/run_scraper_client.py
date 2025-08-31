import grpc
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.scrapqt import services_pb2
from src.scrapqt import services_pb2_grpc

def run_scraper_client(query_text):
    print(f"Attempting to scrape for query: '{query_text}'")
    with grpc.insecure_channel('localhost:60002') as channel:
        stub = services_pb2_grpc.ScraperStub(channel)
        try:
            response = stub.Scrape(services_pb2.ScrapeRequest(query=query_text))
            print(f"Scrape Response: Success={response.success}, Items Scraped={response.items_scraped}")
        except grpc.RpcError as e:
            print(f"Error during scraping: {e.details()}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "gaming keyboard" # Default query
        print("No query provided. Using default query: 'gaming keyboard'")
    run_scraper_client(query)