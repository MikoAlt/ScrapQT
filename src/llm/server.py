import grpc
from concurrent import futures
import time
import os
import google.generativeai as genai
import sqlite3
from dotenv import load_dotenv
import signal
import sys
import hashlib

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.scrapqt import services_pb2
from src.scrapqt import services_pb2_grpc
from db_config import DB_CONFIG

DATABASE_PATH = DB_CONFIG.database_path

def init_db():
    """Initializes the database and creates the products table if it doesn't exist."""
    # Directory creation is already handled by DB_CONFIG
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price REAL,
            review_score REAL,
            review_count INTEGER,
            link TEXT,
            ecommerce TEXT,
            is_used BOOLEAN,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sentiment_score REAL,
            description TEXT,
            query_id INTEGER,
            image_url TEXT,
            url_hash TEXT UNIQUE
        )
    """)
    
    # Create product_queries junction table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            query_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (query_id) REFERENCES queries(id),
            UNIQUE(product_id, query_id)
        )
    """)
    
    # Add sentiment_score column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN sentiment_score REAL")
        print("Added 'sentiment_score' column to 'products' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("'sentiment_score' column already exists.")
        else:
            raise e
    
    # Add description column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN description TEXT")
        print("Added 'description' column to 'products' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("'description' column already exists.")
        else:
            raise e
    
    # Add query_id column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN query_id INTEGER")
        print("Added 'query_id' column to 'products' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("'query_id' column already exists.")
        else:
            raise e
    
    # Add image_url column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN image_url TEXT")
        print("Added 'image_url' column to 'products' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("'image_url' column already exists.")
        else:
            raise e
    
    # Add url_hash column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN url_hash TEXT")
        print("Added 'url_hash' column to 'products' table.")
        
        # Create unique index on url_hash separately
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_products_url_hash_unique ON products(url_hash)")
        print("Created unique index on 'url_hash' column.")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("'url_hash' column already exists.")
            # Ensure the unique index exists even if column already exists
            try:
                cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_products_url_hash_unique ON products(url_hash)")
                print("Ensured unique index on 'url_hash' column.")
            except sqlite3.Error as idx_error:
                print(f"Index creation error: {idx_error}")
        else:
            raise e
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("'description' column already exists.")
        else:
            raise e

    # Create queries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Queries table initialized.")

    # Create query_links table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            primary_query_id INTEGER,
            linked_query_id INTEGER,
            relationship_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (primary_query_id) REFERENCES queries(id),
            FOREIGN KEY (linked_query_id) REFERENCES queries(id)
        )
    """)
    print("Query_links table initialized.")

    # Add query_id to products table
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN query_id INTEGER")
        print("Added 'query_id' column to 'products' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("'query_id' column already exists.")
        else:
            raise e
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_query_id ON products (query_id)")
        print("Created index on 'query_id' in 'products' table.")
    except sqlite3.OperationalError as e:
        print(f"Error creating index on 'query_id': {e}")

    conn.commit()
    conn.close()
    print("Database initialized.")

class SentimentServicer(services_pb2_grpc.SentimentServicer):
    """Provides methods that implement functionality of sentiment analysis server."""

    def __init__(self):
        load_dotenv() # Load environment variables from .env
        self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            print("ERROR: GEMINI_API_KEY not configured in environment variables.")
        else:
            genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def _refresh_api_key(self):
        """Refresh API key from environment variables"""
        new_api_key = os.getenv("GEMINI_API_KEY")
        if new_api_key != self.api_key:
            self.api_key = new_api_key
            if self.api_key:
                genai.configure(api_key=self.api_key)
                print("API key updated from environment variables.")
            else:
                print("Warning: GEMINI_API_KEY no longer available in environment.")

    def Analyze(self, request, context):
        """Analyzes the sentiment of a given text using the Gemini API."""
        # Refresh API key in case it was updated in environment
        self._refresh_api_key()
        
        if not self.api_key:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details("GEMINI_API_KEY not configured on the server.")
            return services_pb2.SentimentResponse()

        print(f"Sentiment service received request to analyze: '{request.text[:50]}...'")

        prompt = f"""Analyze the sentiment of the following text and return a single integer score from 1 (very negative) to 10 (very positive). Only return the integer, nothing else.

        Text: "{request.text}"
        Score: """

        try:
            response = self.model.generate_content(prompt)
            score_text = response.text.strip()
            score = int(score_text)
            if 1 <= score <= 10:
                print(f"  - Returning score from Gemini: {score}")
                return services_pb2.SentimentResponse(score=score)
            else:
                raise ValueError("Score out of range")
        except Exception as e:
            print(f"Error calling Gemini API or parsing response: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error processing sentiment: {e}")
            return services_pb2.SentimentResponse()

    def AnalyzeDatabaseSentiment(self, request, context):
        """Analyzes the sentiment of entries in the database."""
        # Refresh API key in case it was updated in environment
        self._refresh_api_key()
        
        if not self.api_key:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details("GEMINI_API_KEY not configured on the server.")
            return services_pb2.AnalyzeDatabaseSentimentResponse(items_analyzed=0)

        print("Sentiment service received request to analyze database entries.")
        conn = None
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Select items that need sentiment analysis (e.g., sentiment_score is NULL or 0)
            cursor.execute("SELECT id, title, description FROM products WHERE sentiment_score IS NULL OR sentiment_score = 0") # Analyze if score is NULL or 0
            items_to_analyze = cursor.fetchall()

            items_analyzed_count = 0
            for item_id, title, description in items_to_analyze:
                text_to_analyze = ""
                if title:
                    text_to_analyze += title
                if description:
                    text_to_analyze += " " + description

                if not text_to_analyze.strip():
                    continue # Skip if no text to analyze

                prompt = f"""Analyze the sentiment of the following text and return a single integer score from 1 (very negative) to 10 (very positive). Only return the integer, nothing else.

                Text: "{text_to_analyze}"
                Score: """

                try:
                    response = self.model.generate_content(prompt)
                    score_text = response.text.strip()
                    score = int(score_text)
                    if 1 <= score <= 10:
                        cursor.execute("UPDATE products SET sentiment_score = ? WHERE id = ?", (score, item_id))
                        items_analyzed_count += 1
                        print(f"  - Analyzed item {item_id}: score={score}")
                    else:
                        print(f"  - Warning: Score out of range for item {item_id}: {score_text}")
                except Exception as e:
                    print(f"  - Error analyzing sentiment for item {item_id}: {e}")
            conn.commit()
            print(f"Successfully analyzed {items_analyzed_count} database entries.")
            return services_pb2.AnalyzeDatabaseSentimentResponse(items_analyzed=items_analyzed_count)
        except Exception as e:
            print(f"Failed to analyze database entries: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Database analysis error: {e}")
            return services_pb2.AnalyzeDatabaseSentimentResponse(items_analyzed=0)
        finally:
            if conn:
                conn.close()

    def _generate_url_hash(self, url: str) -> str:
        """Generate a hash for a URL to detect duplicates"""
        if not url:
            return ""
        # Use SHA-256 hash of the URL
        return hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]  # Use first 16 chars for shorter hash

    def _link_product_to_query(self, conn: sqlite3.Connection, product_id: int, query_id: int):
        """Link a product to a query in the junction table"""
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO product_queries (product_id, query_id)
                VALUES (?, ?)
            """, (product_id, query_id))
        except sqlite3.Error as e:
            print(f"Error linking product {product_id} to query {query_id}: {e}")

    def SaveItems(self, request_iterator, context):
        """Receives a stream of scraped items and saves them to the database, avoiding duplicates."""
        print("LLM service received request to save items.")
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        item_count = 0
        duplicate_count = 0
        
        try:
            for item in request_iterator:
                url_hash = self._generate_url_hash(item.link)
                
                # Check if product with this URL hash already exists
                cursor.execute("SELECT id FROM products WHERE url_hash = ?", (url_hash,))
                existing_product = cursor.fetchone()
                
                if existing_product:
                    # Product already exists - just link it to the current query
                    existing_product_id = existing_product[0]
                    self._link_product_to_query(conn, existing_product_id, item.query_id)
                    duplicate_count += 1
                    print(f"Found duplicate URL: {item.link} - linked to query {item.query_id}")
                else:
                    # New product - insert it
                    # Convert sentiment_score of 0 to None (NULL in database) for unanalyzed items
                    sentiment_value = None if item.sentiment_score == 0 else item.sentiment_score
                    
                    cursor.execute("""
                        INSERT INTO products (title, price, review_score, review_count, link, ecommerce, is_used, sentiment_score, description, query_id, image_url, url_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (item.title, item.price, item.review_score, item.review_count, item.link, item.ecommerce, item.is_used, sentiment_value, item.description, item.query_id, item.image_url, url_hash))
                    
                    # Get the newly inserted product ID and link to query
                    new_product_id = cursor.lastrowid
                    self._link_product_to_query(conn, new_product_id, item.query_id)
                    item_count += 1
                    
            conn.commit()
            print(f"Successfully saved {item_count} new items and linked {duplicate_count} existing items to queries.")
            return services_pb2.SaveStatus(success=True, items_saved=item_count + duplicate_count)
            
        except Exception as e:
            conn.rollback()
            print(f"Failed to save items to database: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Database error: {e}")
            return services_pb2.SaveStatus(success=False, items_saved=0)
        finally:
            conn.close()

    def SaveQuery(self, request, context):
        """Saves a query to the queries table and returns its ID."""
        print(f"LLM service received request to save query: '{request.query_text}'")
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT OR IGNORE INTO queries (query_text) VALUES (?)", (request.query_text,))
            cursor.execute("SELECT id FROM queries WHERE query_text = ?", (request.query_text,))
            query_id = cursor.fetchone()[0]
            conn.commit()
            print(f"Query '{request.query_text}' saved with ID: {query_id}")
            return services_pb2.SaveQueryResponse(query_id=query_id)
        except Exception as e:
            conn.rollback()
            print(f"Failed to save query: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Database error: {e}")
            return services_pb2.SaveQueryResponse(query_id=0)
        finally:
            conn.close()

    def LinkQueries(self, request, context):
        """Links two queries together in the query_links table."""
        print(f"LLM service received request to link primary_query_id={request.primary_query_id} with linked_query_id={request.linked_query_id} ({request.relationship_type})")
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO query_links (primary_query_id, linked_query_id, relationship_type)
                VALUES (?, ?, ?)
            """, (request.primary_query_id, request.linked_query_id, request.relationship_type))
            conn.commit()
            print("Queries linked successfully.")
            return services_pb2.LinkQueriesResponse(success=True)
        except Exception as e:
            conn.rollback()
            print(f"Failed to link queries: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Database error: {e}")
            return services_pb2.LinkQueriesResponse(success=False)
        finally:
            conn.close()

def serve():
    """Starts the integrated gRPC server."""
    print(f"Integrated LLM+DB server using database at: {DATABASE_PATH}")
    
    # Initialize the database
    init_db()
    
    # Start the gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    services_pb2_grpc.add_SentimentServicer_to_server(SentimentServicer(), server)
    server.add_insecure_port('0.0.0.0:60001')
    server.start()
    print("Integrated LLM+DB gRPC server started on port 60001.")

    # Add graceful shutdown handling
    try:
        while True:
            time.sleep(86400) # One day
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Shutting down server gracefully...")
        server.stop(5).wait() # 5-second grace period
        print("Integrated server stopped.")
    except SystemExit: # Handle signals like SIGTERM
        print("SystemExit received. Shutting down server gracefully...")
        server.stop(5).wait() # 5-second grace period
        print("Integrated server stopped.")

# Signal handler function
def signal_handler(signum, frame):
    print(f"Signal {signum} received. Initiating graceful shutdown.")
    raise SystemExit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    serve()