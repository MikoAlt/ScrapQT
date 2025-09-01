import grpc
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scrapqt import services_pb2
from src.scrapqt import services_pb2_grpc

def analyze_text_sentiment(text):
    print(f"\n--- Analyzing sentiment for text: '{text}' ---")
    with grpc.insecure_channel('localhost:60001') as channel:
        stub = services_pb2_grpc.SentimentStub(channel)
        try:
            response = stub.Analyze(services_pb2.SentimentRequest(text=text))
            print(f"Sentiment Score: {response.score}")
        except grpc.RpcError as e:
            print(f"Error analyzing text sentiment: {e.details()}")

def analyze_database_sentiment():
    print("\n--- Analyzing sentiment for database entries ---")
    with grpc.insecure_channel('localhost:60001') as channel:
        stub = services_pb2_grpc.SentimentStub(channel)
        try:
            response = stub.AnalyzeDatabaseSentiment(services_pb2.AnalyzeDatabaseSentimentRequest())
            print(f"Items analyzed in database: {response.items_analyzed}")
        except grpc.RpcError as e:
            print(f"Error analyzing database sentiment: {e.details()}")

if __name__ == '__main__':
    # Test individual text analysis
    analyze_text_sentiment("This product is absolutely fantastic! I love it.")
    analyze_text_sentiment("This is the worst product I have ever bought. Completely useless.")
    analyze_text_sentiment("It's okay, nothing special.")

    # Test database sentiment analysis
    analyze_database_sentiment()
