import sqlite3
import os

DATABASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'scraped_data.db'))

def check_database():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        print("Database content (products table):")
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        for product in products:
            print(product)

        print("\nDatabase content (queries table):")
        cursor.execute("SELECT * FROM queries")
        queries = cursor.fetchall()
        for query in queries:
            print(query)

        print("\nDatabase content (query_links table):")
        cursor.execute("SELECT * FROM query_links")
        query_links = cursor.fetchall()
        for link in query_links:
            print(link)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_database()