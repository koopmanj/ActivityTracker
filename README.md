# Windows Activity Tracker

A lightweight personal activity tracker for Windows that records active window usage, takes periodic screenshots, and generates daily and weekly reports.

## Features

- **Active Window Tracking** -- Logs which application and window title is in the foreground, every 2 seconds
- **Periodic Screenshots** -- Captures the screen every 2 minutes (only when active, not idle)
- **Idle Detection** -- Automatically pauses tracking after 10 minutes of no keyboard/mouse input
- **Day Rollover** -- Automatically starts a new log at midnight
- **Daily HTML Report** -- Dark-themed report with hourly activity chart, application breakdown, timeline, and screenshot gallery
- **Weekly HTML Report** -- Aggregated view of the last 7 days
- **Weekly Work Report Prompt** -- Reusable AI prompt to generate a structured weekly work report from the tracker data
- **Auto-Start via Task Scheduler** -- Runs silently at logon with crash recovery

## Quick Start

### Start Tracking
Double-click **`start-tracker.bat`** or run:
```
python tracker.py
```
Leave it running in the background. Press **Ctrl+C** to stop.

### View Today's Report
Double-click **`view-report.bat`** or run:
```
python report.py
```
Opens an HTML report in your browser.

### View Report for a Specific Date
```
python report.py 2026-02-18
```

### View Weekly Report
```
python report.py --week
```

## Project Structure

```
ActivityTracker/
  data/
    2026-04-14/
      activity.jsonl        # Raw event log (JSON Lines)
      summary.json          # Aggregated daily summary
      report.html           # Generated HTML report
      screenshots/          # Periodic screenshots
        screenshot_104500.jpg
        screenshot_105000.jpg
        ...
    weekly-report.html      # Generated weekly HTML report
  tracker.py                # Main tracker script
  report.py                 # HTML report generator (daily + weekly)
  start-tracker.bat         # Quick-start launcher
  view-report.bat           # Quick report viewer
  setup-task.ps1            # Task Scheduler setup (auto-start + crash recovery)
  weekly-report-prompt.md   # AI prompt for structured weekly work reports
  README.md
```

## Configuration

Edit the top of `tracker.py` to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| `SCREENSHOT_INTERVAL_SECONDS` | 120 (2 min) | How often to take screenshots |
| `ACTIVITY_POLL_INTERVAL_SECONDS` | 2 | How often to check the active window |
| `SCREENSHOT_QUALITY` | 60 | JPEG quality (1-100, lower = smaller files) |
| `SCREENSHOT_SCALE` | 0.5 | Screenshot size scale (0.5 = half resolution) |
| `IDLE_THRESHOLD_SECONDS` | 600 (10 min) | Seconds of no input before marking as idle |

## Auto-Start with Windows

The tracker can run automatically via **Windows Task Scheduler**, which provides:

- **Auto-start at logon** -- launches silently when you sign in (no console window)
- **Crash recovery** -- restarts automatically up to 3 times if the process dies (1-minute interval)
- **Battery-friendly** -- runs on battery power without being stopped
- **Missed-start recovery** -- starts as soon as possible if a trigger was missed (e.g., laptop was asleep)
- **No time limit** -- runs indefinitely until you log off or stop it manually

### Setup (one-time)

Run the setup script from PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File setup-task.ps1
```

The script auto-detects your Python installation and project directory. It registers a scheduled task named **ActivityTracker** that:

1. Locates `pythonw.exe` on your PATH (runs without a console window)
2. Removes any existing task with the same name (safe to re-run)
3. Creates a task action running `pythonw.exe tracker.py` in the project directory
4. Sets the trigger to fire at logon for the current user
5. Configures resilience settings (battery, restart on crash, no timeout)
6. Registers and verifies the task

### Managing the task

```powershell
# Start the tracker now (without waiting for next logon)
Start-ScheduledTask -TaskName "ActivityTracker"

# Check task status
Get-ScheduledTask -TaskName "ActivityTracker" | Format-List

# Stop the tracker
Stop-ScheduledTask -TaskName "ActivityTracker"

# Remove the task entirely
Unregister-ScheduledTask -TaskName "ActivityTracker" -Confirm:$false
```

You can also manage it via the Task Scheduler GUI: press `Win+R`, type `taskschd.msc`, find **ActivityTracker** in the root folder.

### Why Task Scheduler and not a Windows Service?

A Windows Service runs in **Session 0** -- an isolated session with no desktop access. The tracker needs to read the active foreground window, capture screenshots, and detect keyboard/mouse idle state. None of these work from Session 0. Task Scheduler runs the task in the user's desktop session, giving it full access to the interactive desktop.

### Alternative: Startup folder (simpler, no crash recovery)

1. Press **Win+R**, type `shell:startup`, press Enter
2. Create a shortcut to `start-tracker.bat` in that folder
3. Right-click the shortcut, go to Properties, set "Run" to **Minimized**

## Weekly Work Report Generation

The file `weekly-report-prompt.md` contains a reusable AI prompt for generating a structured weekly work report from the tracker data. This is separate from the HTML weekly report -- it produces a narrative markdown document suitable for sharing with stakeholders.

### Usage

1. Collect the `summary.json` files for each day of the target week from `data/`
2. Paste the prompt from `weekly-report-prompt.md` into Claude or another AI assistant
3. Attach or paste the `summary.json` contents for each day
4. Optionally include `activity.jsonl` files for richer detail
5. Save the output as `data/weekly-work-report-2026-WXX.md`

The prompt extracts work context from window titles (Teams chats, Confluence pages, Jira tickets, VS Code projects, etc.) and classifies activities into work streams.

## Privacy & Storage Notes

- **All data stays local** -- nothing is sent anywhere
- Screenshots at default settings use ~50-150 KB each (~30-90 MB/day at 2-minute intervals)
- Activity logs are typically <1 MB/day
- Delete any day's data by removing its folder from `data/`

## Requirements

- Windows 10/11
- Python 3.8+
- Packages: `pillow`, `psutil`, `pywin32`, `mss`
