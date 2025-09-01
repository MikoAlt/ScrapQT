import os
import importlib.util
import sys

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import grpc
from src.scrapqt import services_pb2
from src.scrapqt import services_pb2_grpc
import sqlite3

from src.scraper.base_scraper import BaseScraper
from db_config import DB_CONFIG

DATABASE_PATH = DB_CONFIG.database_path

def load_plugins(plugin_dir: str) -> list[BaseScraper]:
    """
    Loads all scraper plugins from the specified directory.

    Args:
        plugin_dir: The directory where the plugins are located.

    Returns:
        A list of instantiated scraper plugins.
    """
    plugins = []
    for filename in os.listdir(plugin_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            plugin_path = os.path.join(plugin_dir, filename)
            module_name = filename[:-3]

            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    if isinstance(attribute, type) and issubclass(attribute, BaseScraper) and attribute is not BaseScraper:
                        plugins.append(attribute())
    return plugins

def generate_scraped_items(plugins, query, query_id):
    """Generator function to yield scraped items with enhanced data handling."""
    for plugin in plugins:
        print(f"Scraping with plugin: {plugin.ecommerce_name}")
        scraped_data = plugin.scrape(query)

        for item_data in scraped_data:
            # Use the description from scraper if available, otherwise create a basic one
            description = item_data.get('description', f"High-quality {item_data['title']} available on {plugin.ecommerce_name}")
            
            # Ensure we have all required fields with proper defaults
            yield services_pb2.ScrapedItem(
                title=item_data.get('title', 'Unknown Product'),
                price=float(item_data.get('price', 0.0)),
                review_score=float(item_data.get('review_score', 0.0)),
                review_count=int(item_data.get('review_count', 0)),
                link=item_data.get('link', ''),
                ecommerce=plugin.ecommerce_name,
                is_used=bool(item_data.get('is_used', False)),
                description=description,
                query_id=query_id,
                image_url=item_data.get('image_url', ''),
                sentiment_score=0,  # Set to 0 explicitly - will be stored as NULL in database for unanalyzed items
            )

def scrape_and_save_linked_queries(primary_query_id, primary_query_text, db_stub, loaded_plugins): # Removed sentiment_stub
    print(f"\n--- Scraping linked queries for '{primary_query_text}' (ID: {primary_query_id}) ---")
    conn = sqlite3.connect(DATABASE_PATH) # Need DATABASE_PATH here
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT linked_query_id, relationship_type FROM query_links WHERE primary_query_id = ?", (primary_query_id,))
        linked_queries_data = cursor.fetchall()
        conn.close()

        if not linked_queries_data:
            print(f"No linked queries found for '{primary_query_text}'.")
            return

        for linked_query_id, relationship_type in linked_queries_data:
            conn = sqlite3.connect(DATABASE_PATH) # Re-open connection for each linked query
            cursor = conn.cursor() # Re-open cursor for each linked query
            cursor.execute("SELECT query_text FROM queries WHERE id = ?", (linked_query_id,))
            linked_query_text = cursor.fetchone()[0]
            conn.close()

            print(f"  Scraping linked query: '{linked_query_text}' (Relationship: {relationship_type})")
            item_list = list(generate_scraped_items(loaded_plugins, linked_query_text, primary_query_id)) # Removed sentiment_stub
            try:
                status = db_stub.SaveItems(iter(item_list))
                print(f"  Database service response for linked query: success={status.success}, items_saved={status.items_saved}")
            except grpc.RpcError as e:
                print(f"  Could not connect to Database service for linked query: {e.details()}")

            # Recursively scrape linked queries of this linked query
            scrape_and_save_linked_queries(linked_query_id, linked_query_text, db_stub, loaded_plugins) # Removed sentiment_stub

    except Exception as e:
        print(f"Error processing linked queries for '{primary_query_text}': {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print(f"Loading services_pb2 from: {services_pb2.__file__}")

    # --- Call Scraper Service ---
    print("\n--- Calling Scraper Service ---")
    with grpc.insecure_channel('localhost:60002') as channel: # Scraper service on port 60002
        scraper_stub = services_pb2_grpc.ScraperStub(channel)
        query = "gaming laptop"
        try:
            response = scraper_stub.Scrape(services_pb2.ScrapeRequest(query=query))
            print(f"Scraper service response: success={response.success}, items_scraped={response.items_scraped}")
        except grpc.RpcError as e:
            print(f"Could not connect to Scraper service: {e.details()}")

    # --- Call Sentiment Analysis Service (direct calls for testing) ---
    print("\n--- Calling Sentiment Analysis Service (direct calls for testing) ---")
    with grpc.insecure_channel('localhost:60001') as channel:
        stub = services_pb2_grpc.SentimentStub(channel)
        try:
            response = stub.Analyze(services_pb2.SentimentRequest(text="This product is amazing! I love it."))
            print(f"Sentiment service response: score={response.score}")
        except grpc.RpcError as e:
            print(f"Could not connect to Sentiment service: {e.details()}")

    # --- Call AnalyzeDatabaseSentiment Service (direct calls for testing) ---
    print("\n--- Calling AnalyzeDatabaseSentiment Service (direct calls for testing) ---")
    with grpc.insecure_channel('localhost:60001') as channel:
        stub = services_pb2_grpc.SentimentStub(channel)
        try:
            response = stub.AnalyzeDatabaseSentiment(services_pb2.AnalyzeDatabaseSentimentRequest())
            print(f"AnalyzeDatabaseSentiment service response: items_analyzed={response.items_analyzed}")
        except grpc.RpcError as e:
            print(f"Could not connect to Sentiment service: {e.details()}")
