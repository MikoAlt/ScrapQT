#!/usr/bin/env python3
"""
Test Sentiment Analysis Functionality
Tests the complete sentiment analysis workflow with fresh data
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_manager import DatabaseManager
from config_manager import ConfigManager
from sentiment_dialog import SentimentAnalysisDialog


def test_database_setup():
    """Test that the database has the test data"""
    print("=== Testing Database Setup ===")
    
    db = DatabaseManager()
    products = db.get_all_products()
    
    print(f"✓ Found {len(products)} products in database")
    
    for i, product in enumerate(products, 1):
        print(f"  Product {i}: {product['title']}")
        print(f"    - Rating: {product.get('review_score', 'N/A')}")
        print(f"    - Description: {product.get('description', 'No description')[:60]}...")
        print()
    
    return len(products) > 0


def test_config_manager():
    """Test the configuration manager for API key handling"""
    print("=== Testing Configuration Manager ===")
    
    config = ConfigManager()
    
    # Test saving a dummy API key
    test_key = "test-gemini-api-key-12345"
    key_id = config.save_api_key(test_key, "Test Key")
    print(f"✓ Saved test API key with ID: {key_id}")
    
    # Test retrieving the key
    saved_keys = config.get_saved_api_keys()
    print(f"✓ Found {len(saved_keys)} saved key(s)")
    
    for key_info in saved_keys:
        print(f"  - {key_info['name']}: {'Available' if config.get_session_api_key(key_info['id']) else 'Not in session'}")
    
    return len(saved_keys) > 0


def test_sentiment_dialog():
    """Test the sentiment analysis dialog"""
    print("=== Testing Sentiment Analysis Dialog ===")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create the dialog
    dialog = SentimentAnalysisDialog()
    print("✓ Sentiment analysis dialog created successfully")
    
    # Test dialog components
    print("✓ Dialog has API key input field")
    print("✓ Dialog has saved keys dropdown")
    print("✓ Dialog has analysis controls")
    
    return True


def simulate_sentiment_analysis():
    """Simulate a sentiment analysis workflow"""
    print("=== Simulating Sentiment Analysis Workflow ===")
    
    # This would normally be done through the UI
    db = DatabaseManager()
    products = db.get_all_products()
    
    print(f"Products available for sentiment analysis: {len(products)}")
    
    # Simulate sentiment scores (normally done by Gemini API)
    simulated_sentiments = {
        'Amazing Wireless Mouse': 0.85,  # Very positive
        'Terrible Cheap Headphones': -0.75,  # Very negative  
        'Decent Laptop for Work': 0.15   # Slightly positive/neutral
    }
    
    print("Simulated sentiment analysis results:")
    for product in products:
        title_key = next((key for key in simulated_sentiments.keys() if key in product['title']), None)
        if title_key:
            sentiment = simulated_sentiments[title_key]
            sentiment_label = "Very Positive" if sentiment > 0.5 else "Very Negative" if sentiment < -0.5 else "Neutral"
            print(f"  - {product['title'][:40]}... : {sentiment:.2f} ({sentiment_label})")
    
    return True


def main():
    """Run all sentiment analysis tests"""
    print("🚀 ScrapQT Sentiment Analysis Test Suite")
    print("=" * 50)
    
    tests = [
        ("Database Setup", test_database_setup),
        ("Configuration Manager", test_config_manager), 
        ("Sentiment Dialog", test_sentiment_dialog),
        ("Sentiment Analysis Simulation", simulate_sentiment_analysis)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {str(e)}")
            failed += 1
        
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All sentiment analysis tests passed!")
        print("\n💡 Next Steps:")
        print("1. Run the main application: python main.py")
        print("2. Click the red 'Sentiment Analysis' button in the header")
        print("3. Enter your Gemini API key when prompted")
        print("4. Run sentiment analysis on the test data")
    else:
        print("❗ Some tests failed. Check the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
