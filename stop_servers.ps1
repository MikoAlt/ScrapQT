# stop_servers.ps1
# This script reads PIDs from run_servers_pids.txt and terminates them.

$pidFilePath = Join-Path $PSScriptRoot "run_servers_pid.txt"
Write-Host "Looking for PID file at: $pidFilePath" # New line

if (Test-Path $pidFilePath) {
    $pids = Get-Content $pidFilePath | Where-Object { $_ -match "^\d+$" }

    if ($pids.Length -gt 0) {
        Write-Host "Attempting to terminate processes with PIDs: $($pids -join ', ')"
        foreach ($processId in $pids) { # Changed $pid to $processId
            try {
                Stop-Process -Id $processId -Force -ErrorAction Stop
                Write-Host "Successfully terminated process with PID: $processId"
            } catch {
                Write-Warning "Could not terminate process with PID: $processId. Error: $($_.Exception.Message)"
            }
        }
        Remove-Item $pidFilePath -ErrorAction SilentlyContinue
        Write-Host "PID file removed."
    } else {
        Write-Host "No PIDs found in $pidFilePath."
    }
} else {
    Write-Host "PID file not found: $pidFilePath"
}