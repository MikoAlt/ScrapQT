"""
Database Manager for ScrapQT UI
Provides direct SQLite database access without gRPC
"""

import sqlite3
import os
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from db_config import DB_CONFIG


class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file. If None, uses default path.
        """
        if db_path is None:
            self.db_path = DB_CONFIG.database_path
        else:
            self.db_path = db_path
            # Only create directory for custom paths (default is handled by DB_CONFIG)
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database schema
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema if it doesn't exist"""
        with DB_CONFIG.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create products table
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
            
            # Create queries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_text TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create product_queries junction table for many-to-many relationship
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
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_query_id ON products (query_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_ecommerce ON products (ecommerce)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_scraped_at ON products (scraped_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_url_hash ON products (url_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_queries_product_id ON product_queries (product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_queries_query_id ON product_queries (query_id)")
            
            # Migration: Add image_url column if it doesn't exist
            try:
                cursor.execute("ALTER TABLE products ADD COLUMN image_url TEXT")
            except sqlite3.OperationalError:
                # Column already exists, continue
                pass
            
            # Migration: Add url_hash column if it doesn't exist
            try:
                cursor.execute("ALTER TABLE products ADD COLUMN url_hash TEXT UNIQUE")
                print("Added url_hash column to products table")
            except sqlite3.OperationalError:
                # Column already exists, continue
                pass
            
            # Migration: Populate url_hash for existing products
            cursor.execute("SELECT id, link FROM products WHERE url_hash IS NULL")
            products_without_hash = cursor.fetchall()
            
            for product_id, link in products_without_hash:
                if link:
                    url_hash = self._generate_url_hash(link)
                    try:
                        cursor.execute("UPDATE products SET url_hash = ? WHERE id = ?", (url_hash, product_id))
                    except sqlite3.IntegrityError:
                        # Duplicate URL hash found - this product is a duplicate
                        print(f"Found duplicate URL during migration: {link}")
                        # We could handle this by removing the duplicate, but for now just skip
                        pass
            
            conn.commit()
    
    def _generate_url_hash(self, url: str) -> str:
        """Generate a hash for a URL to detect duplicates"""
        if not url:
            return ""
        # Use SHA-256 hash of the URL
        return hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]  # Use first 16 chars for shorter hash
    
    def get_duplicate_statistics(self) -> Dict[str, int]:
        """Get statistics about duplicate URLs in the database"""
        with DB_CONFIG.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count products with same URL hash
            cursor.execute("""
                SELECT url_hash, COUNT(*) as count
                FROM products 
                WHERE url_hash IS NOT NULL AND url_hash != ''
                GROUP BY url_hash
                HAVING COUNT(*) > 1
                ORDER BY count DESC
            """)
            
            duplicates = cursor.fetchall()
            
            # Count total products and unique URLs
            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT url_hash) FROM products WHERE url_hash IS NOT NULL AND url_hash != ''")
            unique_urls = cursor.fetchone()[0]
            
            return {
                'total_products': total_products,
                'unique_urls': unique_urls,
                'duplicate_groups': len(duplicates),
                'total_duplicates': sum(count for _, count in duplicates) if duplicates else 0
            }
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """
        Get all products from the database
        
        Returns:
            List of product dictionaries
        """
        with DB_CONFIG.get_connection() as conn:
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.*, q.query_text
                FROM products p
                LEFT JOIN queries q ON p.query_id = q.id
                ORDER BY p.scraped_at DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_products_by_query(self, query_text: str) -> List[Dict[str, Any]]:
        """
        Get products by query text
        
        Args:
            query_text: The search query text
            
        Returns:
            List of product dictionaries
        """
        with DB_CONFIG.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.*, q.query_text
                FROM products p
                LEFT JOIN queries q ON p.query_id = q.id
                WHERE q.query_text LIKE ?
                ORDER BY p.scraped_at DESC
            """, (f"%{query_text}%",))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_products_by_ecommerce(self, ecommerce: str) -> List[Dict[str, Any]]:
        """
        Get products by e-commerce platform
        
        Args:
            ecommerce: E-commerce platform name
            
        Returns:
            List of product dictionaries
        """
        with DB_CONFIG.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.*, q.query_text
                FROM products p
                LEFT JOIN queries q ON p.query_id = q.id
                WHERE p.ecommerce = ?
                ORDER BY p.scraped_at DESC
            """, (ecommerce,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def search_products(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search products by matching queries in the queries table
        Uses the product_queries junction table for many-to-many relationships
        
        Args:
            search_term: Term to search for in queries
            
        Returns:
            List of matching product dictionaries from matching queries
        """
        with DB_CONFIG.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Find matching queries, then get all products linked to those queries
            cursor.execute("""
                SELECT DISTINCT p.*, q.query_text
                FROM products p
                INNER JOIN product_queries pq ON p.id = pq.product_id
                INNER JOIN queries q ON pq.query_id = q.id
                WHERE q.query_text LIKE ?
                ORDER BY q.query_text, p.scraped_at DESC
            """, (f"%{search_term}%",))
            
            rows = cursor.fetchall()
            products = [dict(row) for row in rows]
            
            # If no results found using junction table, fallback to direct query_id lookup
            if not products:
                cursor.execute("""
                    SELECT p.*, q.query_text
                    FROM products p
                    INNER JOIN queries q ON p.query_id = q.id
                    WHERE q.query_text LIKE ?
                    ORDER BY q.query_text, p.scraped_at DESC
                """, (f"%{search_term}%",))
                
                rows = cursor.fetchall()
                products = [dict(row) for row in rows]
            
            return products
    
    def get_fuzzy_query_suggestions(self, search_term: str, limit: int = 10) -> List[str]:
        """
        Get fuzzy search suggestions for queries
        
        Args:
            search_term: Partial search term
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested query strings
        """
        if not search_term or len(search_term.strip()) < 1:
            return []
            
        search_term = search_term.lower().strip()
        
        with DB_CONFIG.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all unique queries
            cursor.execute("SELECT DISTINCT query_text FROM queries ORDER BY query_text")
            all_queries = [row[0] for row in cursor.fetchall()]
            
            # Simple fuzzy matching using string similarity
            suggestions = []
            
            # Exact matches first
            for query in all_queries:
                if search_term in query.lower():
                    suggestions.append(query)
            
            # If we don't have enough exact matches, add partial word matches
            if len(suggestions) < limit:
                for query in all_queries:
                    if query not in suggestions:
                        query_words = query.lower().split()
                        search_words = search_term.split()
                        
                        # Check if any search word is a prefix of any query word
                        for search_word in search_words:
                            for query_word in query_words:
                                if query_word.startswith(search_word) or search_word in query_word:
                                    suggestions.append(query)
                                    break
                            if query in suggestions:
                                break
            
            # Remove duplicates while preserving order
            seen = set()
            unique_suggestions = []
            for suggestion in suggestions:
                if suggestion not in seen:
                    seen.add(suggestion)
                    unique_suggestions.append(suggestion)
            
            return unique_suggestions[:limit]
    
    def get_all_unique_queries(self, limit: int = 50) -> List[str]:
        """
        Get all unique queries from the database
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of all unique query strings ordered by most recent first
        """
        with DB_CONFIG.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all unique queries ordered by most recent first
            cursor.execute("""
                SELECT query_text 
                FROM queries 
                GROUP BY query_text
                ORDER BY MAX(created_at) DESC 
                LIMIT ?
            """, (limit,))
            
            return [row[0] for row in cursor.fetchall()]
    
    def get_product_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary with various statistics
        """
        with DB_CONFIG.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total products
            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]
            
            # Products by platform
            cursor.execute("""
                SELECT ecommerce, COUNT(*) as count
                FROM products
                GROUP BY ecommerce
                ORDER BY count DESC
            """)
            platforms = dict(cursor.fetchall())
            
            # Average price
            cursor.execute("SELECT AVG(price) FROM products WHERE price > 0")
            avg_price_result = cursor.fetchone()[0]
            avg_price = avg_price_result if avg_price_result else 0
            
            # Average sentiment score
            cursor.execute("SELECT AVG(sentiment_score) FROM products WHERE sentiment_score > 0")
            avg_sentiment_result = cursor.fetchone()[0]
            avg_sentiment = avg_sentiment_result if avg_sentiment_result else 0
            
            # Products with sentiment analysis
            cursor.execute("SELECT COUNT(*) FROM products WHERE sentiment_score IS NOT NULL AND sentiment_score > 0")
            products_with_sentiment = cursor.fetchone()[0]
            
            return {
                'total_products': total_products,
                'platforms': platforms,
                'average_price': round(avg_price, 2),
                'average_sentiment': round(avg_sentiment, 2),
                'products_with_sentiment': products_with_sentiment
            }
    
    def delete_product(self, product_id: int) -> bool:
        """
        Delete a product by ID, including all related records
        
        Args:
            product_id: ID of the product to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with DB_CONFIG.get_connection() as conn:
                cursor = conn.cursor()
                
                # First, delete from product_queries junction table
                cursor.execute("DELETE FROM product_queries WHERE product_id = ?", (product_id,))
                print(f"Deleted {cursor.rowcount} entries from product_queries for product {product_id}")
                
                # Then delete the product itself
                cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
                product_deleted = cursor.rowcount > 0
                
                if product_deleted:
                    print(f"Successfully deleted product {product_id}")
                else:
                    print(f"No product found with ID {product_id}")
                
                conn.commit()
                return product_deleted
                
        except Exception as e:
            print(f"Error deleting product {product_id}: {e}")
            return False
    
    def clear_all_data(self) -> bool:
        """
        Clear all data from the database (products, queries, query_links)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with DB_CONFIG.get_connection() as conn:
                cursor = conn.cursor()
                
                # First, delete junction table entries (they reference both products and queries)
                cursor.execute("DELETE FROM product_queries")
                
                # Then delete products (they may reference queries)
                cursor.execute("DELETE FROM products")
                
                # Finally delete queries and query_links
                cursor.execute("DELETE FROM query_links")
                cursor.execute("DELETE FROM queries")
                
                conn.commit()
                print("Successfully cleared all data from database tables")
                return True
        except Exception as e:
            print(f"Error clearing database: {e}")
            return False
    
    def get_unique_ecommerce_platforms(self) -> List[str]:
        """
        Get list of unique e-commerce platforms
        
        Returns:
            List of platform names
        """
        with DB_CONFIG.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT ecommerce FROM products WHERE ecommerce IS NOT NULL ORDER BY ecommerce")
            return [row[0] for row in cursor.fetchall()]
    
    def get_recent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent search queries
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of query dictionaries
        """
        with DB_CONFIG.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT q.*, COUNT(p.id) as product_count
                FROM queries q
                LEFT JOIN products p ON q.id = p.query_id
                GROUP BY q.id
                ORDER BY q.created_at DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_product_sentiment(self, product_id: int, sentiment_score: float) -> bool:
        """
        Update sentiment score for a specific product
        
        Args:
            product_id: ID of the product to update
            sentiment_score: Sentiment score (typically -1.0 to 1.0)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with DB_CONFIG.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE products 
                    SET sentiment_score = ?
                    WHERE id = ?
                """, (sentiment_score, product_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating sentiment for product {product_id}: {e}")
            return False
