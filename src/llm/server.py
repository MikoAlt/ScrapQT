import grpc
from concurrent import futures
import time
import os
import google.generativeai as genai
import sqlite3 # New import
from dotenv import load_dotenv # New import


from src.scrapqt import services_pb2
from src.scrapqt import services_pb2_grpc

DATABASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'scraped_data.db')) # New line

class SentimentServicer(services_pb2_grpc.SentimentServicer):
    """Provides methods that implement functionality of sentiment analysis server."""

    def __init__(self):
        load_dotenv() # Load environment variables from .env
        self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            print("ERROR: GEMINI_API_KEY not configured in environment variables.")
        else:
            genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def Analyze(self, request, context):
        """Analyzes the sentiment of a given text using the Gemini API."""
        if not self.api_key:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details("GEMINI_API_KEY not configured on the server.")
            return services_pb2.SentimentResponse()

        print(f"Sentiment service received request to analyze: '{request.text[:50]}...'")

        prompt = f"""Analyze the sentiment of the following text and return a single integer score from 1 (very negative) to 10 (very positive). Only return the integer, nothing else.

        Text: "{request.text}"
        Score: """

        try:
            response = self.model.generate_content(prompt)
            score_text = response.text.strip()
            score = int(score_text)
            if 1 <= score <= 10:
                print(f"  - Returning score from Gemini: {score}")
                return services_pb2.SentimentResponse(score=score)
            else:
                raise ValueError("Score out of range")
        except Exception as e:
            print(f"Error calling Gemini API or parsing response: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error processing sentiment: {e}")
            return services_pb2.SentimentResponse()

    def AnalyzeDatabaseSentiment(self, request, context):
        """Analyzes the sentiment of entries in the database."""
        if not self.api_key:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details("GEMINI_API_KEY not configured on the server.")
            return services_pb2.AnalyzeDatabaseSentimentResponse(items_analyzed=0)

        print("Sentiment service received request to analyze database entries.")
        conn = None
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Select items that need sentiment analysis (e.g., sentiment_score is NULL or 0)
            cursor.execute("SELECT id, title, description FROM products WHERE sentiment_score IS NULL OR sentiment_score = 0") # Analyze if score is NULL or 0
            items_to_analyze = cursor.fetchall()

            items_analyzed_count = 0
            for item_id, title, description in items_to_analyze:
                text_to_analyze = ""
                if title:
                    text_to_analyze += title
                if description:
                    text_to_analyze += " " + description

                if not text_to_analyze.strip():
                    continue # Skip if no text to analyze

                prompt = f"""Analyze the sentiment of the following text and return a single integer score from 1 (very negative) to 10 (very positive). Only return the integer, nothing else.

                Text: "{text_to_analyze}"
                Score: """

                try:
                    response = self.model.generate_content(prompt)
                    score_text = response.text.strip()
                    score = int(score_text)
                    if 1 <= score <= 10:
                        cursor.execute("UPDATE products SET sentiment_score = ? WHERE id = ?", (score, item_id))
                        items_analyzed_count += 1
                        print(f"  - Analyzed item {item_id}: score={score}")
                    else:
                        print(f"  - Warning: Score out of range for item {item_id}: {score_text}")
                except Exception as e:
                    print(f"  - Error analyzing sentiment for item {item_id}: {e}")
            conn.commit()
            print(f"Successfully analyzed {items_analyzed_count} database entries.")
            return services_pb2.AnalyzeDatabaseSentimentResponse(items_analyzed=items_analyzed_count)
        except Exception as e:
            print(f"Failed to analyze database entries: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Database analysis error: {e}")
            return services_pb2.AnalyzeDatabaseSentimentResponse(items_analyzed=0)
        finally:
            if conn:
                conn.close()

def serve():
    """Starts the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    services_pb2_grpc.add_SentimentServicer_to_server(SentimentServicer(), server)
    server.add_insecure_port('0.0.0.0:60001')
    server.start()
    print("Sentiment gRPC server started on port 60001.")
    try:
        while True:
            time.sleep(86400) # One day
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()