import sqlite3
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from db_config import DB_CONFIG

DATABASE_PATH = DB_CONFIG.database_path

def check_sentiment_scores():
    """Check the sentiment scores in the database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("Checking sentiment scores in the database...")
    print("=" * 50)
    
    # Get all products with their sentiment scores
    cursor.execute("""
        SELECT id, title, sentiment_score, query_id, scraped_at 
        FROM products 
        ORDER BY scraped_at DESC 
        LIMIT 15
    """)
    
    products = cursor.fetchall()
    
    for product_id, title, sentiment_score, query_id, scraped_at in products:
        sentiment_status = "NULL (unanalyzed)" if sentiment_score is None else f"{sentiment_score} (analyzed)"
        print(f"ID: {product_id}, Title: {title[:40]}..., Sentiment: {sentiment_status}, Query ID: {query_id}")
    
    # Count by sentiment status
    cursor.execute("SELECT COUNT(*) FROM products WHERE sentiment_score IS NULL")
    unanalyzed_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE sentiment_score IS NOT NULL AND sentiment_score > 0")
    analyzed_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE sentiment_score = 0")
    zero_count = cursor.fetchone()[0]
    
    print("\n" + "=" * 50)
    print(f"Summary:")
    print(f"  Unanalyzed (NULL): {unanalyzed_count}")
    print(f"  Analyzed (1-10): {analyzed_count}")
    print(f"  Zero scores: {zero_count}")
    
    conn.close()

if __name__ == "__main__":
    check_sentiment_scores()
