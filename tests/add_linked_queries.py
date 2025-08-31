import grpc
from src.scrapqt import services_pb2
from src.scrapqt import services_pb2_grpc
import time

def run_add_linked_queries():
    with grpc.insecure_channel('localhost:60000') as channel:
        db_stub = services_pb2_grpc.DatabaseStub(channel)

        # Save primary queries
        print("Saving primary queries...")
        resp_gaming_laptop = db_stub.SaveQuery(services_pb2.SaveQueryRequest(query_text="gaming laptop"))
        gaming_laptop_id = resp_gaming_laptop.query_id
        print(f"Gaming Laptop ID: {gaming_laptop_id}")

        resp_gaming_mouse = db_stub.SaveQuery(services_pb2.SaveQueryRequest(query_text="gaming mouse"))
        gaming_mouse_id = resp_gaming_mouse.query_id
        print(f"Gaming Mouse ID: {gaming_mouse_id}")

        resp_gaming_keyboard = db_stub.SaveQuery(services_pb2.SaveQueryRequest(query_text="gaming keyboard"))
        gaming_keyboard_id = resp_gaming_keyboard.query_id
        print(f"Gaming Keyboard ID: {gaming_keyboard_id}")

        resp_mouse_pad = db_stub.SaveQuery(services_pb2.SaveQueryRequest(query_text="mouse pad"))
        mouse_pad_id = resp_mouse_pad.query_id
        print(f"Mouse Pad ID: {mouse_pad_id}")

        # Link queries
        print("\nLinking queries...")
        db_stub.LinkQueries(services_pb2.LinkQueriesRequest(primary_query_id=gaming_laptop_id, linked_query_id=gaming_mouse_id, relationship_type="related"))
        db_stub.LinkQueries(services_pb2.LinkQueriesRequest(primary_query_id=gaming_laptop_id, linked_query_id=gaming_keyboard_id, relationship_type="related"))
        db_stub.LinkQueries(services_pb2.LinkQueriesRequest(primary_query_id=gaming_mouse_id, linked_query_id=mouse_pad_id, relationship_type="related"))
        print("Queries linked successfully.")

if __name__ == '__main__':
    run_add_linked_queries()
