from database_manager import DatabaseManager
import sqlite3

# Sample image URLs for testing
sample_images = [
    "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400",  # Laptop
    "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400",   # Headphones
    "https://images.unsplash.com/photo-1527814050087-3793815479db?w=400"    # Mouse
]

dm = DatabaseManager()
products = dm.get_all_products()

# Update products with sample image URLs
for i, product in enumerate(products):
    if i < len(sample_images):
        # Update the product with an image URL
        with sqlite3.connect(dm.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE products SET image_url = ? WHERE id = ?",
                (sample_images[i], product['id'])
            )
            conn.commit()
        print(f"Updated product {product['id']} with image: {sample_images[i]}")

print("Sample image URLs added to products for testing hover functionality!")
