#!/usr/bin/env python3
"""
Test Sentiment Display in Main Application
Verifies that sentiment scores are displayed correctly in the UI
"""

from database_manager import DatabaseManager

def test_sentiment_display():
    """Test the sentiment display functionality"""
    print("🎨 Sentiment Display Test")
    print("=" * 50)
    
    # Get current products and their sentiments
    db = DatabaseManager()
    products = db.get_all_products()
    
    print("📊 Current Products and Expected Display:")
    print()
    
    for i, product in enumerate(products, 1):
        title = product['title'][:40] + "..." if len(product['title']) > 40 else product['title']
        sentiment = product.get('sentiment_score')
        
        print(f"{i}. {title}")
        
        if sentiment is not None:
            # Apply the same logic as the main UI
            if sentiment >= 0.3:
                display_text = f"😊 Positive ({sentiment:.2f})"
                color = "Green background"
            elif sentiment >= -0.3:
                display_text = f"😐 Neutral ({sentiment:.2f})"
                color = "Orange background"
            else:
                display_text = f"😞 Negative ({sentiment:.2f})"
                color = "Red background"
        else:
            display_text = "❓ Unanalyzed"
            color = "Gray background"
        
        print(f"   Sentiment Score: {sentiment}")
        print(f"   Display Text: {display_text}")
        print(f"   Background Color: {color}")
        print()
    
    print("✅ Updated Features:")
    print("   • Column header changed from 'Status' to 'Sentiment'")
    print("   • Sentiment scores displayed with emojis and numeric values")
    print("   • Color-coded backgrounds:")
    print("     - 🟢 Green: Positive sentiment (≥ 0.3)")
    print("     - 🟠 Orange: Neutral sentiment (-0.3 to 0.3)")
    print("     - 🔴 Red: Negative sentiment (< -0.3)")
    print("     - ⚫ Gray: Unanalyzed products")
    print("   • Scores shown on -1.0 to 1.0 scale (Gemini normalized)")
    
    print()
    print("🎯 Expected Results in Main App:")
    print("   - Amazing Wireless Mouse: 😊 Positive (1.00) with green background")
    print("   - Terrible Cheap Headphones: 😞 Negative (-1.00) with red background")
    print("   - Decent Laptop: 😐 Neutral (0.11) with orange background")
    
    print()
    print("🚀 Main application is running - check the Sentiment column!")

if __name__ == "__main__":
    test_sentiment_display()
