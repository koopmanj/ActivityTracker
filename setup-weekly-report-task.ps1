# ============================================================================
# Weekly Report — Task Scheduler Setup
# ============================================================================
# Registers a scheduled task that generates the weekly activity report
# every Monday at 09:00 via Claude Code CLI.
#
# Usage:  powershell -ExecutionPolicy Bypass -File setup-weekly-report-task.ps1
# Remove: Unregister-ScheduledTask -TaskName "ActivityTrackerWeeklyReport" -Confirm:$false
# ============================================================================

$ErrorActionPreference = "Stop"

$taskName = "ActivityTrackerWeeklyReport"
$trackerDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptPath = Join-Path $trackerDir "generate-weekly-report.ps1"

# --- Step 1: Remove existing task if present ---

Write-Host "[Step 1] Checking for existing '$taskName' task..." -ForegroundColor Cyan

$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "  Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "  Removed." -ForegroundColor Green
} else {
    Write-Host "  No existing task found." -ForegroundColor Green
}

# --- Step 2: Define the task action ---

Write-Host "[Step 2] Defining task action..." -ForegroundColor Cyan

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`"" `
    -WorkingDirectory "$trackerDir"

Write-Host "  Script: $scriptPath" -ForegroundColor Green

# --- Step 3: Define the trigger (every Monday at 09:00) ---

Write-Host "[Step 3] Defining trigger (weekly, Monday 09:00)..." -ForegroundColor Cyan

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "09:00"

Write-Host "  Trigger: Every Monday at 09:00" -ForegroundColor Green

# --- Step 4: Define task settings ---

Write-Host "[Step 4] Configuring task settings..." -ForegroundColor Cyan

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15)

Write-Host "  AllowStartIfOnBatteries:    True" -ForegroundColor Green
Write-Host "  StartWhenAvailable:         True (runs on next logon if missed)" -ForegroundColor Green
Write-Host "  ExecutionTimeLimit:         15 minutes" -ForegroundColor Green

# --- Step 5: Register the task ---

Write-Host "[Step 5] Registering scheduled task '$taskName'..." -ForegroundColor Cyan

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Generates a weekly activity report via Claude Code CLI every Monday at 09:00. Shows a toast notification when ready."

Write-Host "  Task '$taskName' registered successfully!" -ForegroundColor Green

# --- Step 6: Verify ---

Write-Host "[Step 6] Verifying..." -ForegroundColor Cyan

$task = Get-ScheduledTask -TaskName $taskName
Write-Host "  Task Name:   $($task.TaskName)" -ForegroundColor Green
Write-Host "  State:       $($task.State)" -ForegroundColor Green

# --- Done ---

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Setup complete!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The weekly report will generate every Monday at 09:00."
Write-Host "If your laptop is off/asleep, it runs at next logon."
Write-Host ""
Write-Host "To run it now:"
Write-Host "  Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Yellow
Write-Host ""
Write-Host "To remove:"
Write-Host "  Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false" -ForegroundColor Yellow
