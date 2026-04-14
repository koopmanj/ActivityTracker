# ============================================================================
# Weekly Report Generator
# ============================================================================
# Collects last week's ActivityTracker data, generates a narrative weekly
# report via Claude Code CLI, and shows a Windows toast notification.
#
# Usage:  powershell -ExecutionPolicy Bypass -File generate-weekly-report.ps1
# ============================================================================

$ErrorActionPreference = "Stop"

$trackerDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$dataDir = Join-Path $trackerDir "data"
$reportDir = Join-Path $trackerDir "report"
$promptFile = Join-Path $reportDir "weekly-report-prompt.md"

# --- Step 1: Determine last week's date range (Mon-Sun) ---

$today = Get-Date
# Always target the PREVIOUS completed week's Monday (7-13 days ago)
$daysSinceMonday = (($today.DayOfWeek.value__ + 6) % 7)  # 0=Mon, 1=Tue, ..., 6=Sun
$lastMonday = $today.AddDays(-$daysSinceMonday - 7)

$cal = [System.Globalization.CultureInfo]::InvariantCulture.Calendar
$weekNumber = $cal.GetWeekOfYear(
    $lastMonday,
    [System.Globalization.CalendarWeekRule]::FirstFourDayWeek,
    [System.DayOfWeek]::Monday
)

$dates = 0..6 | ForEach-Object { $lastMonday.AddDays($_).ToString("yyyy-MM-dd") }
$weekLabel = "W{0:D2}" -f $weekNumber
$yearLabel = $lastMonday.ToString("yyyy")
$reportFile = Join-Path $reportDir "weekly-work-report-$yearLabel-$weekLabel.md"

Write-Host "[Step 1] Target week: $weekLabel ($($dates[0]) to $($dates[6]))" -ForegroundColor Cyan

# --- Step 2: Collect summary.json files ---

Write-Host "[Step 2] Collecting summary.json files..." -ForegroundColor Cyan

$summaryData = ""
$daysFound = 0

foreach ($date in $dates) {
    $summaryFile = Join-Path $dataDir "$date\summary.json"
    if (Test-Path $summaryFile) {
        $content = Get-Content $summaryFile -Raw
        $summaryData += "`n=== $date ===`n$content`n"
        $daysFound++
        Write-Host "  Found: $date" -ForegroundColor Green
    }
}

if ($daysFound -eq 0) {
    Write-Host "  No data found for last week. Skipping report generation." -ForegroundColor Yellow
    exit 0
}

Write-Host "  Collected data for $daysFound day(s)" -ForegroundColor Green

# --- Step 3: Read the prompt template ---

Write-Host "[Step 3] Reading prompt template..." -ForegroundColor Cyan

if (-not (Test-Path $promptFile)) {
    Write-Host "  ERROR: Prompt file not found: $promptFile" -ForegroundColor Red
    exit 1
}

# Extract the prompt content between the first ``` and the closing ```
$promptRaw = Get-Content $promptFile -Raw
# The prompt is between the first ``` after "## Prompt" and the ``` before "## Quick Usage Guide"
$promptMatch = [regex]::Match($promptRaw, '(?s)## Prompt\s*```\s*(.+?)```\s*---\s*## Quick Usage Guide')
if ($promptMatch.Success) {
    $promptTemplate = $promptMatch.Groups[1].Value.Trim()
} else {
    # Fallback: use everything between first ``` pair
    $promptMatch = [regex]::Match($promptRaw, '(?s)```\s*(.+?)```')
    $promptTemplate = $promptMatch.Groups[1].Value.Trim()
}

Write-Host "  Prompt loaded ($($promptTemplate.Length) chars)" -ForegroundColor Green

# --- Step 4: Build the full prompt with data ---

Write-Host "[Step 4] Generating report via Claude Code CLI..." -ForegroundColor Cyan

$fullPrompt = @"
$promptTemplate

## Attached Data

$summaryData
"@

# Write prompt to a temp file (avoids command-line length limits)
$tempFile = Join-Path $env:TEMP "weekly-report-prompt-$(Get-Random).txt"
$fullPrompt | Out-File -FilePath $tempFile -Encoding UTF8

# --- Step 5: Invoke Claude Code CLI ---

try {
    $reportContent = Get-Content $tempFile -Raw | & claude -p --output-format text 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Claude CLI returned exit code $LASTEXITCODE" -ForegroundColor Red
        Write-Host $reportContent -ForegroundColor Red
        exit 1
    }
} finally {
    Remove-Item $tempFile -ErrorAction SilentlyContinue
}

Write-Host "  Report generated ($($reportContent.Length) chars)" -ForegroundColor Green

# --- Step 6: Save the report ---

Write-Host "[Step 5] Saving report..." -ForegroundColor Cyan

if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}

$reportContent | Out-File -FilePath $reportFile -Encoding UTF8
Write-Host "  Saved: $reportFile" -ForegroundColor Green

# --- Step 7: Show Windows toast notification ---

Write-Host "[Step 6] Showing notification..." -ForegroundColor Cyan

$xml = @"
<toast activationType="protocol" launch="file:///$($reportFile -replace '\\','/')">
  <visual>
    <binding template="ToastGeneric">
      <text>Weekly Report Ready</text>
      <text>Your $weekLabel activity report ($daysFound day(s) tracked) is ready. Click to open.</text>
    </binding>
  </visual>
</toast>
"@

try {
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null

    $toastXml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $toastXml.LoadXml($xml)

    $appId = "ActivityTracker"
    $toast = [Windows.UI.Notifications.ToastNotification]::new($toastXml)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show($toast)

    Write-Host "  Notification sent!" -ForegroundColor Green
} catch {
    Write-Host "  Toast notification failed: $_" -ForegroundColor Yellow
    Write-Host "  Report is still available at: $reportFile" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Done. Report: $reportFile" -ForegroundColor Cyan
