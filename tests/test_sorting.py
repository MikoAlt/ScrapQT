#!/usr/bin/env python3
"""
Test script to verify table sorting functionality
"""

import sys
from PyQt5 import QtWidgets, QtCore
from database_manager import DatabaseManager

def test_sorting():
    """Test the table sorting functionality"""
    print("Testing table sorting functionality...")
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Get all products to test sorting
    products = db_manager.get_all_products()
    print(f"Total products in database: {len(products)}")
    
    # Display product data for verification
    print("\nProduct data for sorting test:")
    print("=" * 80)
    for i, product in enumerate(products):
        rating = product.get('review_score', 0) if product.get('review_score') else 0
        price = product.get('price', 0) if product.get('price') else 0
        sentiment = product.get('sentiment_score')
        sentiment_str = f"{sentiment:.3f}" if sentiment is not None else "None"
        
        print(f"{i+1}. {product.get('title', '')[:40]:<40} | "
              f"Platform: {product.get('ecommerce', 'N/A'):<10} | "
              f"Rating: {rating:<5.1f} | "
              f"Price: ${price:<8.2f} | "
              f"Sentiment: {sentiment_str}")
    
    print("\nSorting test scenarios:")
    print("1. Click 'Product Name' header - should sort alphabetically")
    print("2. Click 'Platform' header - should sort by platform name") 
    print("3. Click 'Rating' header - should sort by numeric rating (N/A at bottom)")
    print("4. Click 'Amount' header - should sort by price (N/A at bottom)")
    print("5. Click 'Status' header - should sort by sentiment score (Unanalyzed at bottom)")
    print("6. Click same header again - should reverse sort order")
    
    print("\nExpected sorting behaviors:")
    print("- Text columns: Alphabetical A-Z (ascending) or Z-A (descending)")
    print("- Rating column: Lowest to highest (ascending) or highest to lowest (descending)")
    print("- Price column: Cheapest to most expensive (ascending) or vice versa (descending)")
    print("- Sentiment: Most negative to most positive (ascending) or vice versa (descending)")
    print("- N/A and Unanalyzed values should always sort to the bottom")
    
    print("\nVisual indicators:")
    print("- Column headers should show hover effect (blue highlight)")
    print("- Active sort column should show up/down arrow")
    print("- Headers should be clickable with pointer cursor")
    
    return True

if __name__ == "__main__":
    # Test sorting functionality
    test_sorting()
    
    print("\n" + "="*80)
    print("To test interactively:")
    print("1. Run 'python main.py' to start the application")
    print("2. Click on different column headers to test sorting")
    print("3. Click the same header again to reverse the sort order")
    print("4. Verify that numeric columns sort properly (not as strings)")
    print("5. Check that N/A and Unanalyzed values appear at the bottom")
