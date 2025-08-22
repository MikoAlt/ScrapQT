import subprocess
import os
import time
from dotenv import load_dotenv # New import

print(f"Executing run_servers.py from: {os.path.abspath(__file__)}") # New line

load_dotenv() # Load environment variables from .env

# Environment with the API key
env = os.environ.copy()
# env["GEMINI_API_KEY"] = "AIzaSyB1eSr2ESQaqZ4_BAJNdYD8tc-K_AA_WZs" # Removed hardcoded API key

env["GRPC_VERBOSITY"] = "debug"

# Add project root to PYTHONPATH for subprocesses
project_root = os.path.abspath(os.path.dirname(__file__))
if "PYTHONPATH" in env:
    env["PYTHONPATH"] = project_root + os.pathsep + env["PYTHONPATH"]
else:
    env["PYTHONPATH"] = project_root

# Paths to the server scripts
database_server_script = os.path.join('src', 'database', 'server.py')
llm_server_script = os.path.join('src', 'llm', 'server.py')
scraper_server_script = os.path.join('src', 'scraper', 'server.py') # New line
python_executable = os.path.join('.venv', 'Scripts', 'pythonw.exe') # Changed to pythonw.exe

# Output files for the servers
import os

log_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(log_dir, exist_ok=True)

db_server_out = open(os.path.join(log_dir, 'db_server.log'), 'w')
llm_server_out = open(os.path.join(log_dir, 'llm_server.log'), 'w')
scraper_server_out = open(os.path.join(log_dir, 'scraper_server.log'), 'w') # New line

print("Starting database server...")
db_process = subprocess.Popen([python_executable, database_server_script], stdout=db_server_out, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True, env=env, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)

print("Starting sentiment analysis server...")
llm_process = subprocess.Popen([python_executable, llm_server_script], stdout=llm_server_out, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True, env=env, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS) # Removed API key from arguments

print("Starting scraper server...") # New line
scraper_process = subprocess.Popen([python_executable, scraper_server_script], stdout=scraper_server_out, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True, env=env, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS) # New line

time.sleep(2) # Give servers a moment to start

print(f"Database server started with PID: {db_process.pid}")
print(f"Sentiment analysis server started with PID: {llm_process.pid}")
print(f"Scraper server started with PID: {scraper_process.pid}") # New line

print("\nServers are running in the background. Their output is redirected to data/db_server.log, data/llm_server.log, and data/scraper_server.log.") # Modified line
print("To gracefully shut down the servers, use the 'stop_servers.py' script.")
print("\nYou can now run the client in another terminal.")

# Write child PIDs to a file for external termination
pid_file_path = os.path.join(os.path.dirname(__file__), 'run_servers_pid.txt') # Explicit absolute path
print(f"Writing PIDs to: {pid_file_path}") # New line
with open(pid_file_path, "w") as f:
    f.write(str(db_process.pid) + "\n")
    f.write(str(llm_process.pid) + "\n")
    f.write(str(scraper_process.pid) + "\n") # New line

time.sleep(1) # Add a small delay
if os.path.exists(pid_file_path):
    print(f"PID file '{pid_file_path}' exists after writing.")
else:
    print(f"ERROR: PID file '{pid_file_path}' does NOT exist after writing.")

