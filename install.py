import subprocess
import sys
import os

def run_command(command, message):
    print(message)
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)

def create_venv():
    venv_path = os.path.join(os.path.dirname(__file__), '.venv')
    if not os.path.exists(venv_path):
        run_command(f"python -m venv {venv_path}", "Creating virtual environment...")
    else:
        print("Virtual environment already exists.")
    return os.path.join(venv_path, 'Scripts', 'python.exe') # For Windows

def install_dependencies(python_executable):
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    run_command(f"{python_executable} -m pip install -r {requirements_path}", "Installing dependencies...")

def compile_protobuf(python_executable):
    proto_file = os.path.join('src', 'protos', 'services.proto')
    run_command(f"{python_executable} -m grpc_tools.protoc -Isrc/protos --python_out=src/scrapqt --grpc_python_out=src/scrapqt {proto_file}", "Compiling protobuf files...")

def fix_protobuf_imports(python_executable): # New function
    fix_script = os.path.join(os.path.dirname(__file__), 'fix_proto_imports.py')
    run_command(f"{python_executable} {fix_script}", "Fixing protobuf imports...")

if __name__ == "__main__":
    print("Starting installation script...")
    python_executable = create_venv()
    install_dependencies(python_executable)
    compile_protobuf(python_executable)
    fix_protobuf_imports(python_executable) # Call new function
    print("Installation complete. You can now run the servers using 'python run_servers.py'.")