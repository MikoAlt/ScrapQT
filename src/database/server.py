import grpc
from concurrent import futures
import time
import sqlite3
import os # Added import os



from src.scrapqt import services_pb2
from src.scrapqt import services_pb2_grpc

DATABASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'scraped_data.db'))

def init_db():
    """Initializes the database and creates the products table if it doesn't exist."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
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
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN sentiment_score REAL")
        print("Added 'sentiment_score' column to 'products' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("'sentiment_score' column already exists.")
        else:
            raise e
    try: # New block for description
        cursor.execute("ALTER TABLE products ADD COLUMN description TEXT")
        print("Added 'description' column to 'products' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("'description' column already exists.")
        else:
            raise e

    # New: Create queries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Queries table initialized.")

    # New: Create query_links table
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

    # New: Add query_id to products table
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

class DatabaseServicer(services_pb2_grpc.DatabaseServicer):
    """Provides methods that implement functionality of database server."""

    def SaveItems(self, request_iterator, context):
        """Receives a stream of scraped items and saves them to the database."""
        print("Database service received request to save items.")
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        item_count = 0
        try:
            for item in request_iterator:
                cursor.execute("""
                    INSERT INTO products (title, price, review_score, review_count, link, ecommerce, is_used, sentiment_score, description, query_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (item.title, item.price, item.review_score, item.review_count, item.link, item.ecommerce, item.is_used, item.sentiment_score, item.description, item.query_id))
                item_count += 1
            conn.commit()
            print(f"Successfully saved {item_count} items to the database.")
            return services_pb2.SaveStatus(success=True, items_saved=item_count)
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
        print(f"Database service received request to save query: '{request.query_text}'")
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
        print(f"Database service received request to link primary_query_id={request.primary_query_id} with linked_query_id={request.linked_query_id} ({request.relationship_type})")
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

import signal # New import

def serve():
    """Starts the gRPC server."""
    with open(os.path.join(os.path.dirname(DATABASE_PATH), 'db_path.txt'), 'w') as f:
        f.write(DATABASE_PATH)
    print(f"Database server using database at: {DATABASE_PATH}")
    init_db()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    services_pb2_grpc.add_DatabaseServicer_to_server(DatabaseServicer(), server)
    server.add_insecure_port('0.0.0.0:60000')
    server.start()
    print("Database gRPC server started on port 60000.")

    # Add graceful shutdown handling
    try:
        while True:
            time.sleep(86400) # One day
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Shutting down database server gracefully...")
        server.stop(5).wait() # 5-second grace period
        print("Database server stopped.")
    except SystemExit: # Handle signals like SIGTERM
        print("SystemExit received. Shutting down database server gracefully...")
        server.stop(5).wait() # 5-second grace period
        print("Database server stopped.")

# Signal handler function
def signal_handler(signum, frame):
    print(f"Signal {signum} received. Initiating graceful shutdown.")
    raise SystemExit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    serve()

