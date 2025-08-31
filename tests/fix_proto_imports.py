import os
import sys

def fix_imports(file_path):
    print(f"Fixing imports in {file_path}...")
    old_string = "import services_pb2 as services__pb2"
    new_string = "from . import services_pb2 as services__pb2"

    try:
        with open(file_path, 'r') as f:
            content = f.read()

        if old_string in content:
            content = content.replace(old_string, new_string)
            with open(file_path, 'w') as f:
                f.write(content)
            print("Imports fixed successfully.")
        else:
            print("Import string not found, no fix applied (might already be fixed or different).")
    except Exception as e:
        print(f"Error fixing imports in {file_path}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    grpc_pb2_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src', 'scrapqt', 'services_pb2_grpc.py'))
    fix_imports(grpc_pb2_file)