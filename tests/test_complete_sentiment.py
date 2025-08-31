#!/usr/bin/env python3
"""
Complete Sentiment Analysis Test
Tests the full sentiment analysis workflow with gRPC communication
"""

import grpc
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapqt.services_pb2_grpc import LLMServiceStub
from scrapqt.services_pb2 import AnalyzeSentimentRequest
from database_manager import DatabaseManager


def test_grpc_connection():
    """Test if gRPC servers are accessible"""
    print("=== Testing gRPC Connection ===")
    
    try:
        # Test LLM service connection
        channel = grpc.insecure_channel('localhost:50052')
        stub = LLMServiceStub(channel)
        
        # Test with a simple sentiment request
        test_request = AnalyzeSentimentRequest(
            text="This is a test message for connection verification"
        )
        
        # This will fail without a valid API key, but confirms connection
        try:
            response = stub.AnalyzeSentiment(test_request)
            print("✓ gRPC connection successful")
            return True
        except grpc.RpcError as e:
            if "INVALID_ARGUMENT" in str(e) or "API key" in str(e):
                print("✓ gRPC connection successful (API key needed for actual analysis)")
                return True
            else:
                print(f"✗ gRPC connection failed: {e}")
                return False
                
    except Exception as e:
        print(f"✗ gRPC connection failed: {e}")
        return False


def test_database_content():
    """Test database content for sentiment analysis"""
    print("=== Testing Database Content ===")
    
    db = DatabaseManager()
    products = db.get_all_products()
    
    print(f"Found {len(products)} products:")
    
    sentiment_examples = []
    for product in products:
        description = product.get('description', 'No description')
        title = product['title']
        
        # Analyze description content for sentiment indicators
        positive_words = ['amazing', 'fantastic', 'incredible', 'love', 'best', 'great', 'excellent']
        negative_words = ['terrible', 'poor', 'disappointing', 'waste', 'avoid', 'bad', 'awful']
        neutral_words = ['average', 'decent', 'okay', 'basic', 'standard']
        
        pos_count = sum(1 for word in positive_words if word in description.lower())
        neg_count = sum(1 for word in negative_words if word in description.lower())
        neu_count = sum(1 for word in neutral_words if word in description.lower())
        
        if pos_count > neg_count and pos_count > neu_count:
            expected_sentiment = "Positive"
        elif neg_count > pos_count and neg_count > neu_count:
            expected_sentiment = "Negative"
        else:
            expected_sentiment = "Neutral"
        
        print(f"  • {title[:50]}...")
        print(f"    Expected sentiment: {expected_sentiment}")
        print(f"    Description sample: {description[:80]}...")
        print()
        
        sentiment_examples.append({
            'title': title,
            'expected': expected_sentiment,
            'description': description
        })
    
    return sentiment_examples


def generate_test_report():
    """Generate a complete test report"""
    print("🧪 ScrapQT Sentiment Analysis - Complete Test Report")
    print("=" * 60)
    
    # Test 1: gRPC Connection
    grpc_ok = test_grpc_connection()
    print()
    
    # Test 2: Database Content
    examples = test_database_content()
    
    # Test 3: Summary
    print("=== Test Summary ===")
    print(f"✓ gRPC Service: {'Connected' if grpc_ok else 'Failed'}")
    print(f"✓ Database Products: {len(examples)} loaded")
    print(f"✓ Sentiment Analysis Ready: {'Yes' if grpc_ok and examples else 'No'}")
    
    print()
    print("=== Manual Testing Instructions ===")
    print("1. Main application should be running (python main.py)")
    print("2. Click the red 'Sentiment Analysis' button in the header")
    print("3. In the dialog that opens:")
    print("   a. Enter your Gemini API key")
    print("   b. Click 'Start Analysis'")
    print("   c. Watch progress as products are analyzed")
    print()
    print("Expected Results for Test Data:")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['title'][:40]}...")
        print(f"   Expected: {example['expected']} sentiment")
    
    print()
    print("🔧 Troubleshooting:")
    print("- If 'Connection failed': Ensure servers are running (python run_servers.py)")
    print("- If 'API key error': Use a valid Google Gemini API key")
    print("- If 'No products': Database was cleared successfully and has test data")
    
    return grpc_ok and len(examples) > 0


if __name__ == "__main__":
    success = generate_test_report()
    print("\n" + "=" * 60)
    if success:
        print("🎉 Sentiment Analysis System: READY FOR TESTING")
    else:
        print("❌ Sentiment Analysis System: NEEDS ATTENTION")
    
    sys.exit(0 if success else 1)
