import grpc
from concurrent import futures
import time
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.scrapqt import services_pb2
from src.scrapqt import services_pb2_grpc
from src.scraper.base_scraper import BaseScraper
from src.scraper.plugin_loader import load_plugins, generate_scraped_items # Import necessary functions

class ScraperServicer(services_pb2_grpc.ScraperServicer):
    """Provides methods that implement functionality of the scraper server."""

    def __init__(self):
        self.plugin_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'plugins'))
        self.loaded_plugins = load_plugins(self.plugin_directory)
        print(f"Scraper server loaded {len(self.loaded_plugins)} plugins.")

    def Scrape(self, request, context):
        """Initiates a scraping task."""
        print(f"Scraper service received request to scrape: '{request.query}'")
        
        db_channel = None
        # Removed sentiment_channel
        try:
            # Establish gRPC channels to other services
            db_channel = grpc.insecure_channel('localhost:60000')
            db_stub = services_pb2_grpc.DatabaseStub(db_channel)
            
            # Removed sentiment_channel and sentiment_stub creation
            # sentiment_channel = grpc.insecure_channel('localhost:60001')
            # sentiment_stub = services_pb2_grpc.SentimentStub(sentiment_channel)

            # Save query and get query_id
            try:
                save_query_response = db_stub.SaveQuery(services_pb2.SaveQueryRequest(query_text=request.query))
                query_id = save_query_response.query_id
                print(f"  Query '{request.query}' saved with ID: {query_id}")
            except grpc.RpcError as e:
                print(f"  Could not save query: {e.details()}")
                query_id = 0 # Default to 0 if query cannot be saved

            # Generate scraped items and save to DB
            item_list = list(generate_scraped_items(self.loaded_plugins, request.query, query_id)) # Removed sentiment_stub
            
            try:
                status = db_stub.SaveItems(iter(item_list))
                print(f"  Database service response: success={status.success}, items_saved={status.items_saved}")
                return services_pb2.ScrapeResponse(success=status.success, items_scraped=status.items_saved)
            except grpc.RpcError as e:
                print(f"  Could not connect to Database service: {e.details()}")
                return services_pb2.ScrapeResponse(success=False, items_scraped=0)
        finally:
            if db_channel:
                db_channel.close()
            # Removed sentiment_channel close
            # if sentiment_channel:
            #     sentiment_channel.close()

def serve():
    """Starts the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    services_pb2_grpc.add_ScraperServicer_to_server(ScraperServicer(), server)
    server.add_insecure_port('0.0.0.0:60002') # New port for Scraper Service
    server.start()
    print("Scraper gRPC server started on port 60002.")
    try:
        while True:
            time.sleep(86400) # One day
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()