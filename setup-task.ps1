# ============================================================================
# Activity Tracker - Windows Task Scheduler Setup
# ============================================================================
# This script registers a scheduled task that:
#   1. Starts the Activity Tracker automatically at user logon
#   2. Runs silently in the background (no console window)
#   3. Auto-restarts up to 3 times if the process crashes (1-minute interval)
#   4. Runs indefinitely with no execution time limit
#   5. Works on battery power (laptop-friendly)
#
# Usage:  powershell -ExecutionPolicy Bypass -File setup-task.ps1
# Remove: Unregister-ScheduledTask -TaskName "ActivityTracker" -Confirm:$false
# ============================================================================

$ErrorActionPreference = "Stop"

$taskName = "ActivityTracker"
$trackerDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# --- Step 1: Locate pythonw.exe ---
Write-Host "[Step 1] Locating pythonw.exe..." -ForegroundColor Cyan

$pythonw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $pythonw) {
    # Fallback: look next to python.exe
    $python = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
    if ($python) {
        $pythonw = Join-Path (Split-Path $python) "pythonw.exe"
    }
}

if (-not $pythonw -or -not (Test-Path $pythonw)) {
    Write-Host "ERROR: pythonw.exe not found. Ensure Python is installed and on PATH." -ForegroundColor Red
    exit 1
}

Write-Host "  Found: $pythonw" -ForegroundColor Green

# --- Step 2: Remove existing task if present ---
Write-Host "[Step 2] Checking for existing '$taskName' task..." -ForegroundColor Cyan

$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "  Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "  Removed." -ForegroundColor Green
} else {
    Write-Host "  No existing task found." -ForegroundColor Green
}

# --- Step 3: Define the task action ---
Write-Host "[Step 3] Defining task action..." -ForegroundColor Cyan

$action = New-ScheduledTaskAction `
    -Execute "$pythonw" `
    -Argument "`"$trackerDir\tracker.py`"" `
    -WorkingDirectory "$trackerDir"

Write-Host "  Execute:    $pythonw" -ForegroundColor Green
Write-Host "  Argument:   $trackerDir\tracker.py" -ForegroundColor Green
Write-Host "  WorkingDir: $trackerDir" -ForegroundColor Green

# --- Step 4: Define the trigger (at logon) ---
Write-Host "[Step 4] Defining trigger (at logon for current user)..." -ForegroundColor Cyan

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

Write-Host "  Trigger: AtLogOn for user '$env:USERNAME'" -ForegroundColor Green

# --- Step 5: Define task settings ---
Write-Host "[Step 5] Configuring task settings..." -ForegroundColor Cyan

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -RestartCount 3 `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)

Write-Host "  AllowStartIfOnBatteries:    True" -ForegroundColor Green
Write-Host "  DontStopIfGoingOnBatteries: True" -ForegroundColor Green
Write-Host "  StartWhenAvailable:         True" -ForegroundColor Green
Write-Host "  RestartInterval:            1 minute" -ForegroundColor Green
Write-Host "  RestartCount:               3" -ForegroundColor Green
Write-Host "  ExecutionTimeLimit:         Unlimited" -ForegroundColor Green

# --- Step 6: Register the task ---
Write-Host "[Step 6] Registering scheduled task '$taskName'..." -ForegroundColor Cyan

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Runs the Windows Activity Tracker at logon. Tracks active windows, takes periodic screenshots, and logs all activity silently in the background."

Write-Host "  Task '$taskName' registered successfully!" -ForegroundColor Green

# --- Step 7: Verify ---
Write-Host "[Step 7] Verifying task registration..." -ForegroundColor Cyan

$task = Get-ScheduledTask -TaskName $taskName
Write-Host "  Task Name:   $($task.TaskName)" -ForegroundColor Green
Write-Host "  State:       $($task.State)" -ForegroundColor Green
Write-Host "  URI:         $($task.URI)" -ForegroundColor Green

# --- Done ---
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Setup complete!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The tracker will start automatically at your next logon."
Write-Host "To start it right now, run:"
Write-Host "  Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Yellow
Write-Host ""
Write-Host "To check status:"
Write-Host "  Get-ScheduledTask -TaskName '$taskName' | Format-List" -ForegroundColor Yellow
Write-Host ""
Write-Host "To remove:"
Write-Host "  Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false" -ForegroundColor Yellow
