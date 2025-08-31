#!/usr/bin/env python3
"""
Database schema inspector for ScrapQT
"""

import sqlite3

def inspect_database():
    """Inspect the ScrapQT database schema and content"""
    db_path = 'd:/Workspace/ScrapQT/data/scraped_data.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print('=== PRODUCTS TABLE SCHEMA ===')
        cursor.execute('PRAGMA table_info(products)')
        columns = cursor.fetchall()
        
        for col in columns:
            col_id, name, data_type, not_null, default_val, primary_key = col
            print(f'{name:<20} {data_type:<10} | NotNull: {bool(not_null):<5} | Default: {default_val} | PK: {bool(primary_key)}')
        
        print('\n=== SAMPLE PRODUCT DATA ===')
        cursor.execute('SELECT id, title, price, link, ecommerce, image_url FROM products LIMIT 3')
        products = cursor.fetchall()
        
        for i, product in enumerate(products, 1):
            product_id, title, price, link, ecommerce, image_url = product
            print(f'\nProduct {i}:')
            print(f'  ID: {product_id}')
            print(f'  Title: {title[:50]}{"..." if len(title) > 50 else ""}')
            print(f'  Price: {price}')
            print(f'  Link: {link[:60]}{"..." if link and len(link) > 60 else ""}')
            print(f'  Platform: {ecommerce}')
            print(f'  Image URL: {image_url[:60] if image_url else "None"}{"..." if image_url and len(image_url) > 60 else ""}')
        
        print('\n=== ALL COLUMN NAMES ===')
        cursor.execute('SELECT * FROM products LIMIT 1')
        column_names = [description[0] for description in cursor.description]
        print(', '.join(column_names))
        
        print('\n=== DATABASE STATISTICS ===')
        cursor.execute('SELECT COUNT(*) FROM products')
        total_products = cursor.fetchone()[0]
        print(f'Total products: {total_products}')
        
        cursor.execute('SELECT COUNT(DISTINCT ecommerce) FROM products WHERE ecommerce IS NOT NULL')
        platforms = cursor.fetchone()[0]
        print(f'Unique platforms: {platforms}')
        
        cursor.execute('SELECT COUNT(*) FROM products WHERE link IS NOT NULL AND link != ""')
        products_with_links = cursor.fetchone()[0]
        print(f'Products with links: {products_with_links}')
        
        cursor.execute('SELECT COUNT(*) FROM products WHERE image_url IS NOT NULL AND image_url != ""')
        products_with_images = cursor.fetchone()[0]
        print(f'Products with image URLs: {products_with_images}')
        
        conn.close()
        
        print('\n=== FIELD ANALYSIS FOR VIEW BUTTON ===')
        print('Fields that could be useful for a "View" button:')
        print('- link: Product page URL (primary use case)')
        print('- image_url: Product image URL')
        print('- title: Product name for display')
        print('- ecommerce: Platform name')
        print('- price: Product price')
        print('- description: Product details (if available)')
        
    except Exception as e:
        print(f'Error inspecting database: {e}')

if __name__ == "__main__":
    inspect_database()
