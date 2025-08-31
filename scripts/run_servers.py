import subprocess
import os
import sys
import time
from dotenv import load_dotenv

print(f"Executing run_servers.py from: {os.path.abspath(__file__)}")

# Change to project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_root)
print(f"Changed working directory to: {os.getcwd()}")

# Check if servers are already running and stop them first
pid_file_path = os.path.join('scripts', 'run_servers_pid.txt')
if os.path.exists(pid_file_path):
    print("Found existing PID file. Stopping running servers first...")
    stop_script = os.path.join('scripts', 'stop_servers.py')
    try:
        subprocess.run([sys.executable, stop_script], check=True)
        print("Successfully stopped existing servers.")
        time.sleep(2)  # Give processes time to fully terminate
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to stop existing servers: {e}")
        print("Continuing with server startup...")

load_dotenv() # Load environment variables from .env

# Environment with the API key
env = os.environ.copy()

env["GRPC_VERBOSITY"] = "debug"

# Add project root to PYTHONPATH for subprocesses
if "PYTHONPATH" in env:
    env["PYTHONPATH"] = project_root + os.pathsep + env["PYTHONPATH"]
else:
    env["PYTHONPATH"] = project_root

# Paths to the server scripts (database server is now integrated into LLM server)
llm_server_script = os.path.join('src', 'llm', 'server.py')
scraper_server_script = os.path.join('src', 'scraper', 'server.py')
python_executable = os.path.join('.venv', 'Scripts', 'pythonw.exe')

# Output files for the servers
log_dir = os.path.join('data')
os.makedirs(log_dir, exist_ok=True)

llm_server_out = open(os.path.join(log_dir, 'llm_server.log'), 'w')
scraper_server_out = open(os.path.join(log_dir, 'scraper_server.log'), 'w')

print("Starting integrated LLM+Database server...")
llm_process = subprocess.Popen([python_executable, llm_server_script], stdout=llm_server_out, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True, env=env, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)

print("Starting scraper server...")
scraper_process = subprocess.Popen([python_executable, scraper_server_script], stdout=scraper_server_out, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True, env=env, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)

time.sleep(2) # Give servers a moment to start

print(f"Integrated LLM+Database server started with PID: {llm_process.pid}")
print(f"Scraper server started with PID: {scraper_process.pid}")

print("\nServers are running in the background. Their output is redirected to data/llm_server.log and data/scraper_server.log.")
print("To gracefully shut down the servers, use the 'stop_servers.py' script.")
print("\nYou can now run the PyQt UI application.")

# Write child PIDs to a file for external termination
pid_file_path = os.path.join('scripts', 'run_servers_pid.txt')
print(f"Writing PIDs to: {pid_file_path}")
with open(pid_file_path, "w") as f:
    f.write(str(llm_process.pid) + "\n")
    f.write(str(scraper_process.pid) + "\n")

time.sleep(1) # Add a small delay
if os.path.exists(pid_file_path):
    print(f"PID file '{pid_file_path}' exists after writing.")
else:
    print(f"ERROR: PID file '{pid_file_path}' does NOT exist after writing.")

