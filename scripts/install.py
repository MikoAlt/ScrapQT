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

# Get project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(f"Project root: {project_root}")

def create_venv():
    # Point to root directory for .venv
    venv_path = os.path.join(project_root, '.venv')
    if not os.path.exists(venv_path):
        run_command(f"python -m venv {venv_path}", "Creating virtual environment...")
    else:
        print("Virtual environment already exists.")
    return os.path.join(venv_path, 'Scripts', 'python.exe') # For Windows

def install_dependencies(python_executable):
    # Point to root directory for requirements.txt
    requirements_path = os.path.join(project_root, 'requirements.txt')
    run_command(f"{python_executable} -m pip install -r {requirements_path}", "Installing dependencies...")

if __name__ == "__main__":
    print("Starting installation script...")
    python_executable = create_venv()
    install_dependencies(python_executable)
    print("Installation complete. You can now run the application using 'python main.py'.")