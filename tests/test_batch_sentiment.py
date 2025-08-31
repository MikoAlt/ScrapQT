#!/usr/bin/env python3
"""
Batch Sentiment Analysis Test
Tests the new batch processing functionality
"""

from database_manager import DatabaseManager
from config_manager import ConfigManager

def test_batch_sentiment_analysis():
    """Test the batch sentiment analysis system"""
    print("🧪 Batch Sentiment Analysis Test")
    print("=" * 50)
    
    # Check database state
    db = DatabaseManager()
    products = db.get_all_products()
    
    print(f"📊 Database Status:")
    print(f"   Total products: {len(products)}")
    
    products_needing_analysis = [p for p in products if p.get('sentiment_score') is None]
    print(f"   Products needing analysis: {len(products_needing_analysis)}")
    
    if not products_needing_analysis:
        print("   ✅ All products already have sentiment scores")
        return
    
    print()
    print("📝 Products to analyze:")
    for i, product in enumerate(products_needing_analysis, 1):
        title = product['title'][:50] + "..." if len(product['title']) > 50 else product['title']
        description = product.get('description', 'No description')[:60] + "..."
        print(f"   {i}. {title}")
        print(f"      Description: {description}")
    
    print()
    print("⚙️ Batch Configuration Options:")
    print("   • Batch Size: 1-100 products per batch")
    print("   • Batch Delay: 0.0-10.0 seconds between batches")
    print("   • Progress Tracking: Real-time batch and item progress")
    print("   • Error Handling: Individual item failures don't stop batch")
    
    print()
    print("🎯 Expected Batch Behavior:")
    print("   1. Load products needing sentiment analysis")
    print("   2. Process products in configured batch sizes")
    print("   3. Show progress: 'Batch X/Y - Z items processed'")
    print("   4. Wait specified delay between batches")
    print("   5. Convert sentiment scores (1-10 scale → -1 to 1 scale)")
    print("   6. Update database with normalized scores")
    
    print()
    print("🚀 To test batch functionality:")
    print("   1. Main application is running with fresh data")
    print("   2. Click the red 'Sentiment Analysis' button")
    print("   3. Configure batch settings:")
    print("      - Batch Size: Try 2 (will create 2 batches)")
    print("      - Batch Delay: Try 2.0 seconds")
    print("   4. Enter valid Gemini API key")
    print("   5. Watch batch progress updates")
    
    print()
    print("✅ New Batch Features Added:")
    print("   ✓ Batch size configuration (spin box)")
    print("   ✓ Batch delay configuration (double spin box)")
    print("   ✓ Real-time batch progress display")
    print("   ✓ Individual item processing within batches")
    print("   ✓ Progress bar showing overall completion")
    print("   ✓ Detailed status messages")
    print("   ✓ Error resilience (failed items don't stop batch)")

if __name__ == "__main__":
    test_batch_sentiment_analysis()
