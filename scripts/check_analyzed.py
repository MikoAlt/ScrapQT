import sqlite3
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from db_config import DB_CONFIG

DATABASE_PATH = DB_CONFIG.database_path

def check_analyzed_sentiment():
    """Check which products got sentiment analysis"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("Recently analyzed products (sentiment 1-10):")
    print("=" * 60)
    
    # Get products with analyzed sentiments
    cursor.execute("""
        SELECT id, title, sentiment_score, query_id, scraped_at 
        FROM products 
        WHERE sentiment_score >= 1 AND sentiment_score <= 10
        ORDER BY scraped_at DESC 
        LIMIT 10
    """)
    
    products = cursor.fetchall()
    
    for product_id, title, sentiment_score, query_id, scraped_at in products:
        print(f"ID: {product_id}, Title: {title[:50]}..., Sentiment: {sentiment_score}, Query ID: {query_id}")
    
    # Check if any products have descriptions
    print("\nProducts that were analyzed (description check):")
    print("=" * 60)
    cursor.execute("""
        SELECT id, title, description, sentiment_score
        FROM products 
        WHERE sentiment_score >= 1 AND sentiment_score <= 10
        LIMIT 5
    """)
    
    products_with_desc = cursor.fetchall()
    
    for product_id, title, description, sentiment_score in products_with_desc:
        desc_preview = (description[:100] + "...") if description and len(description) > 100 else (description or "No description")
        print(f"ID: {product_id}")
        print(f"  Title: {title}")
        print(f"  Description: {desc_preview}")
        print(f"  Sentiment: {sentiment_score}")
        print()
    
    conn.close()

if __name__ == "__main__":
    check_analyzed_sentiment()
