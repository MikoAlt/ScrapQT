import os
import importlib.util
import sys

# Add the project root to the Python path (MUST BE AT THE VERY TOP)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import grpc # Moved from inside if __name__ == '__main__':
from src.scrapqt import services_pb2 # Moved from inside if __name__ == '__main__':
from src.scrapqt import services_pb2_grpc # Moved from inside if __name__ == '__main__':
import sqlite3 # Moved from inside if __name__ == '__main__':

from src.scraper.base_scraper import BaseScraper

DATABASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'scraped_data.db')) # Moved from inside if __name__ == '__main__':

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

def generate_scraped_items(plugins, query, query_id): # Removed sentiment_stub
    """Generator function to yield scraped items."""
    for plugin in plugins:
        print(f"Scraping with plugin: {plugin.ecommerce_name}")
        scraped_data = plugin.scrape(query)

        for item_data in scraped_data:
            # sentiment_score will be 0 by default for int32, or can be omitted
            yield services_pb2.ScrapedItem(
                title=item_data['title'],
                price=item_data['price'],
                review_score=item_data['review_score'],
                review_count=item_data['review_count'],
                link=item_data['link'],
                ecommerce=plugin.ecommerce_name,
                is_used=item_data['is_used'],
                # sentiment_score is omitted here, will be populated by LLM service
                description="This is a placeholder description for " + item_data['title'], # New field
                query_id=query_id # New field
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
