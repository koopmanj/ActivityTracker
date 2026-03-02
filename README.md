# 📊 Windows Activity Tracker

A lightweight personal activity tracker for Windows that records everything you do on your laptop throughout the day.

## Features

- **🖥️ Active Window Tracking** — Logs which application and window title you're using, every 2 seconds
- **📸 Periodic Screenshots** — Captures your screen every 5 minutes (only when active, not idle)
- **⏸️ Idle Detection** — Automatically pauses tracking when you're away (5 min threshold)
- **📅 Day Rollover** — Automatically starts a new log at midnight
- **📊 Daily HTML Report** — Beautiful dark-themed report with:
  - Total active time & app count
  - Hourly activity chart
  - Application usage breakdown with percentages
  - Activity timeline
  - Screenshot gallery (click to expand)
- **📈 Weekly Report** — Aggregated view of the last 7 days

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

## Data Storage

All data is stored locally in the `data/` folder:

```
activity-tracker/
├── data/
│   ├── 2026-02-18/
│   │   ├── activity.jsonl      # Raw event log (JSON Lines)
│   │   ├── summary.json        # Aggregated summary
│   │   ├── report.html         # Generated HTML report
│   │   └── screenshots/        # Periodic screenshots
│   │       ├── screenshot_104500.jpg
│   │       ├── screenshot_105000.jpg
│   │       └── ...
│   └── 2026-02-19/
│       └── ...
├── tracker.py                  # Main tracker script
├── report.py                   # Report generator
├── start-tracker.bat           # Quick-start launcher
├── view-report.bat             # Quick report viewer
└── README.md
```

## Configuration

Edit the top of `tracker.py` to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| `SCREENSHOT_INTERVAL_SECONDS` | 300 (5 min) | How often to take screenshots |
| `ACTIVITY_POLL_INTERVAL_SECONDS` | 2 | How often to check the active window |
| `SCREENSHOT_QUALITY` | 60 | JPEG quality (1-100, lower = smaller files) |
| `SCREENSHOT_SCALE` | 0.5 | Screenshot size scale (0.5 = half resolution) |
| `IDLE_THRESHOLD_SECONDS` | 300 (5 min) | Seconds of no input before marking as idle |

## Auto-Start with Windows (Optional)

To start tracking automatically when you log in:

1. Press **Win+R**, type `shell:startup`, press Enter
2. Create a shortcut to `start-tracker.bat` in that folder
3. Right-click the shortcut → Properties → set "Run" to **Minimized**

## Privacy & Storage Notes

- **All data stays local** — nothing is sent anywhere
- Screenshots at default settings use ~50-150 KB each (~15-45 MB/day)
- Activity logs are typically <1 MB/day
- Delete any day's data by removing its folder from `data/`

## Requirements

- Windows 10/11
- Python 3.8+
- Packages: `pillow`, `psutil`, `pywin32`, `mss` (auto-installed)
