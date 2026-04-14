"""
Windows Activity Tracker
========================
Tracks active window usage, takes periodic screenshots, and logs all activity.
Run this script to start tracking. Press Ctrl+C to stop.

Data is stored in: ./data/YYYY-MM-DD/
"""

import os
import sys
import json
import time
import signal
import ctypes
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

import psutil
import mss
import mss.tools
from PIL import Image

# Try importing win32 modules
try:
    import win32gui
    import win32process
except ImportError:
    print("ERROR: pywin32 is required. Install with: pip install pywin32")
    sys.exit(1)


# ─── Configuration ───────────────────────────────────────────────────────────

TRACKER_DIR = Path(__file__).parent
DATA_DIR = TRACKER_DIR / "data"
SCREENSHOT_INTERVAL_SECONDS = 120  # Screenshot every 2 minutes
ACTIVITY_POLL_INTERVAL_SECONDS = 2  # Check active window every 2 seconds
SCREENSHOT_QUALITY = 60  # JPEG quality (lower = smaller files)
SCREENSHOT_SCALE = 0.5  # Scale screenshots to 50% size to save space
IDLE_THRESHOLD_SECONDS = 600  # Consider idle after 10 minutes of no input

# ─── Logging Setup ───────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("activity-tracker")


# ─── Idle Detection ─────────────────────────────────────────────────────────

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]


def get_idle_seconds():
    """Get the number of seconds since last user input (mouse/keyboard)."""
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return millis / 1000.0
    return 0


# ─── Active Window Detection ────────────────────────────────────────────────

def get_active_window_info():
    """Get information about the currently active (foreground) window."""
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd == 0:
            return {"title": "No Active Window", "process": "unknown", "pid": 0}

        window_title = win32gui.GetWindowText(hwnd)
        if not window_title:
            window_title = "(untitled)"

        # Get process info
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid)
            process_name = proc.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            process_name = "unknown"

        return {
            "title": window_title,
            "process": process_name,
            "pid": pid,
        }
    except Exception as e:
        log.debug(f"Error getting active window: {e}")
        return {"title": "Unknown", "process": "unknown", "pid": 0}


# ─── Screenshot Capture ─────────────────────────────────────────────────────

def capture_screenshot(save_path: Path):
    """Capture a screenshot and save as compressed JPEG."""
    try:
        with mss.mss() as sct:
            # Capture all monitors
            monitor = sct.monitors[0]  # 0 = all monitors combined
            sct_img = sct.grab(monitor)

            # Convert to PIL Image
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            # Scale down to save space
            if SCREENSHOT_SCALE < 1.0:
                new_size = (
                    int(img.width * SCREENSHOT_SCALE),
                    int(img.height * SCREENSHOT_SCALE),
                )
                img = img.resize(new_size, Image.LANCZOS)

            # Save as JPEG
            save_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(save_path), "JPEG", quality=SCREENSHOT_QUALITY)
            file_size_kb = save_path.stat().st_size / 1024
            log.info(f"📸 Screenshot saved: {save_path.name} ({file_size_kb:.0f} KB)")
            return True
    except Exception as e:
        log.error(f"Screenshot failed: {e}")
        return False


# ─── Activity Logger ────────────────────────────────────────────────────────

class ActivityLogger:
    """Logs window activity to a JSON Lines file."""

    def __init__(self, date_str: str):
        self.date_str = date_str
        self.day_dir = DATA_DIR / date_str
        self.day_dir.mkdir(parents=True, exist_ok=True)

        self.screenshots_dir = self.day_dir / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = self.day_dir / "activity.jsonl"
        self.summary_file = self.day_dir / "summary.json"

        # Current session tracking
        self.current_window = None
        self.current_start = None
        self.sessions = []  # List of completed activity sessions

        log.info(f"📁 Logging to: {self.day_dir}")

    def log_event(self, event_type: str, data: dict):
        """Append an event to the JSONL log file."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            **data,
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def update_activity(self, window_info: dict, is_idle: bool):
        """Track window changes and log activity sessions."""
        now = datetime.now()
        window_key = f"{window_info['process']}|{window_info['title']}"

        if is_idle:
            # If idle, close current session
            if self.current_window is not None:
                self._close_session(now)
                self.current_window = None
                self.current_start = None
                self.log_event("idle_start", {"idle_seconds": get_idle_seconds()})
            return

        if self.current_window is None:
            # Starting fresh (after idle or first run)
            self.current_window = window_key
            self.current_start = now
            self.log_event("window_focus", window_info)
        elif window_key != self.current_window:
            # Window changed
            self._close_session(now)
            self.current_window = window_key
            self.current_start = now
            self.log_event("window_focus", window_info)

    def _close_session(self, end_time: datetime):
        """Close the current activity session and record duration."""
        if self.current_window and self.current_start:
            duration = (end_time - self.current_start).total_seconds()
            parts = self.current_window.split("|", 1)
            session = {
                "process": parts[0],
                "title": parts[1] if len(parts) > 1 else "",
                "start": self.current_start.isoformat(),
                "end": end_time.isoformat(),
                "duration_seconds": round(duration, 1),
            }
            self.sessions.append(session)
            self.log_event("window_blur", session)

    def take_screenshot(self):
        """Take a timestamped screenshot."""
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"screenshot_{timestamp}.jpg"
        save_path = self.screenshots_dir / filename
        if capture_screenshot(save_path):
            self.log_event("screenshot", {"file": filename})

    def save_summary(self):
        """Generate and save a summary of today's activity."""
        now = datetime.now()

        # Close current session for summary
        if self.current_window and self.current_start:
            self._close_session(now)
            # Re-open the session
            self.current_start = now

        # Aggregate by process
        process_time = defaultdict(float)
        process_titles = defaultdict(lambda: defaultdict(float))

        for session in self.sessions:
            proc = session["process"]
            title = session["title"]
            dur = session["duration_seconds"]
            process_time[proc] += dur
            process_titles[proc][title] += dur

        # Sort by total time
        sorted_processes = sorted(process_time.items(), key=lambda x: x[1], reverse=True)

        # Build summary
        total_active = sum(process_time.values())
        summary = {
            "date": self.date_str,
            "generated_at": now.isoformat(),
            "total_active_seconds": round(total_active, 1),
            "total_active_formatted": str(timedelta(seconds=int(total_active))),
            "total_sessions": len(self.sessions),
            "applications": [],
        }

        for proc, total_secs in sorted_processes:
            # Top 5 window titles for this process
            titles_sorted = sorted(
                process_titles[proc].items(), key=lambda x: x[1], reverse=True
            )[:5]

            app_entry = {
                "process": proc,
                "total_seconds": round(total_secs, 1),
                "total_formatted": str(timedelta(seconds=int(total_secs))),
                "percentage": round((total_secs / total_active * 100) if total_active > 0 else 0, 1),
                "top_windows": [
                    {"title": t[:120], "seconds": round(s, 1)} for t, s in titles_sorted
                ],
            }
            summary["applications"].append(app_entry)

        # Count screenshots
        screenshots = list(self.screenshots_dir.glob("*.jpg"))
        summary["screenshot_count"] = len(screenshots)

        with open(self.summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        log.info(f"📊 Summary saved: {len(sorted_processes)} apps, {summary['total_active_formatted']} active time")
        return summary

    def finalize(self):
        """Finalize the day's logging."""
        now = datetime.now()
        if self.current_window and self.current_start:
            self._close_session(now)
        self.log_event("tracker_stop", {"total_sessions": len(self.sessions)})
        self.save_summary()


# ─── Main Tracker Loop ──────────────────────────────────────────────────────

class ActivityTracker:
    """Main tracker that orchestrates activity logging and screenshots."""

    def __init__(self):
        self.running = False
        self.logger = None

    def start(self):
        """Start the activity tracker."""
        self.running = True
        today = datetime.now().strftime("%Y-%m-%d")
        self.logger = ActivityLogger(today)
        self.logger.log_event("tracker_start", {"version": "1.0.0"})

        log.info("=" * 60)
        log.info("🟢 Activity Tracker Started")
        log.info(f"   Polling every {ACTIVITY_POLL_INTERVAL_SECONDS}s")
        log.info(f"   Screenshots every {SCREENSHOT_INTERVAL_SECONDS}s")
        log.info(f"   Idle threshold: {IDLE_THRESHOLD_SECONDS}s")
        log.info(f"   Data directory: {self.logger.day_dir}")
        log.info("   Press Ctrl+C to stop")
        log.info("=" * 60)

        last_screenshot_time = 0
        last_summary_time = time.time()
        summary_interval = 600  # Save summary every 10 minutes

        try:
            while self.running:
                now = time.time()

                # Check for day rollover
                current_date = datetime.now().strftime("%Y-%m-%d")
                if current_date != self.logger.date_str:
                    log.info("📅 Day changed, starting new log...")
                    self.logger.finalize()
                    self.logger = ActivityLogger(current_date)
                    self.logger.log_event("tracker_start", {"version": "1.0.0", "reason": "day_rollover"})

                # Check idle state
                idle_secs = get_idle_seconds()
                is_idle = idle_secs >= IDLE_THRESHOLD_SECONDS

                # Get and log active window
                window_info = get_active_window_info()
                self.logger.update_activity(window_info, is_idle)

                # Periodic screenshot (only when not idle)
                if not is_idle and (now - last_screenshot_time) >= SCREENSHOT_INTERVAL_SECONDS:
                    self.logger.take_screenshot()
                    last_screenshot_time = now

                # Periodic summary save
                if (now - last_summary_time) >= summary_interval:
                    self.logger.save_summary()
                    last_summary_time = now

                time.sleep(ACTIVITY_POLL_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            log.info("\n🔴 Stopping tracker...")
        finally:
            self.stop()

    def stop(self):
        """Stop the tracker and save final data."""
        self.running = False
        if self.logger:
            self.logger.take_screenshot()  # Final screenshot
            self.logger.finalize()
            log.info("✅ Activity tracker stopped. Data saved.")


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tracker = ActivityTracker()
    tracker.start()
