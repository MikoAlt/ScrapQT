import os
import subprocess
import sys

# Get the directory where this script is located (scripts folder)
script_dir = os.path.dirname(__file__)
powershell_script_path = os.path.join(script_dir, "stop_servers.ps1")

print(f"Executing PowerShell script to stop servers: {powershell_script_path}")

try:
    # Execute the PowerShell script
    # -ExecutionPolicy Bypass is needed to run local scripts without signing
    # -File specifies the script to run
    # -NoProfile prevents loading the PowerShell profile, speeding up execution
    # -NonInteractive prevents prompts
    command = [
        "powershell.exe",
        "-ExecutionPolicy", "Bypass",
        "-NoProfile",
        "-NonInteractive",
        "-File", powershell_script_path
    ]
    
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    print("PowerShell script output:")
    print(result.stdout)
    if result.stderr:
        print("PowerShell script errors:")
        print(result.stderr)
    print("Server shutdown process initiated by PowerShell script.")

except subprocess.CalledProcessError as e:
    print(f"Error executing PowerShell script: {e}")
    print(f"Stdout: {e.stdout}")
    print(f"Stderr: {e.stderr}")
    sys.exit(1)
except FileNotFoundError:
    print("Error: powershell.exe not found. Make sure PowerShell is installed and in your PATH.")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)