"""
Daily Activity Report Generator
================================
Generates a beautiful HTML report from the activity tracker data.
Can be run standalone or called from the tracker.

Usage:
    python report.py              # Report for today
    python report.py 2026-02-18   # Report for specific date
    python report.py --week       # Report for the last 7 days
"""

import json
import sys
import os
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

TRACKER_DIR = Path(__file__).parent
DATA_DIR = TRACKER_DIR / "data"


def load_summary(date_str: str) -> dict:
    """Load the summary JSON for a given date."""
    summary_file = DATA_DIR / date_str / "summary.json"
    if not summary_file.exists():
        return None
    with open(summary_file, "r", encoding="utf-8") as f:
        return json.load(f)


def load_activity_log(date_str: str) -> list:
    """Load the raw activity log for a given date."""
    log_file = DATA_DIR / date_str / "activity.jsonl"
    if not log_file.exists():
        return []
    events = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def get_hourly_breakdown(events: list) -> dict:
    """Calculate activity per hour from events."""
    hourly = defaultdict(lambda: defaultdict(float))

    for event in events:
        if event.get("event") == "window_blur":
            try:
                start = datetime.fromisoformat(event["start"])
                duration = event.get("duration_seconds", 0)
                hour = start.strftime("%H:00")
                process = event.get("process", "unknown")
                hourly[hour][process] += duration
            except (KeyError, ValueError):
                continue

    return dict(hourly)


def get_timeline_data(events: list) -> list:
    """Build timeline data for visualization."""
    timeline = []
    for event in events:
        if event.get("event") == "window_blur":
            try:
                start = datetime.fromisoformat(event["start"])
                timeline.append({
                    "time": start.strftime("%H:%M"),
                    "process": event.get("process", "unknown"),
                    "title": event.get("title", "")[:80],
                    "duration": event.get("duration_seconds", 0),
                })
            except (KeyError, ValueError):
                continue
    return timeline


def get_screenshots(date_str: str) -> list:
    """Get list of screenshot files for a date."""
    screenshots_dir = DATA_DIR / date_str / "screenshots"
    if not screenshots_dir.exists():
        return []
    files = sorted(screenshots_dir.glob("*.jpg"))
    return [f.name for f in files]


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def generate_color(index: int) -> str:
    """Generate a distinct color for each application."""
    colors = [
        "#4F46E5", "#059669", "#D97706", "#DC2626", "#7C3AED",
        "#2563EB", "#DB2777", "#0891B2", "#65A30D", "#EA580C",
        "#6366F1", "#14B8A6", "#F59E0B", "#EF4444", "#8B5CF6",
        "#3B82F6", "#EC4899", "#06B6D4", "#84CC16", "#F97316",
    ]
    return colors[index % len(colors)]


def generate_html_report(date_str: str) -> str:
    """Generate a complete HTML report for a given date."""
    summary = load_summary(date_str)
    events = load_activity_log(date_str)
    screenshots = get_screenshots(date_str)
    hourly = get_hourly_breakdown(events)
    timeline = get_timeline_data(events)

    if not summary:
        return f"""<html><body><h1>No data found for {date_str}</h1>
        <p>Make sure the tracker was running on this date.</p></body></html>"""

    apps = summary.get("applications", [])
    total_active = summary.get("total_active_formatted", "0:00:00")
    total_sessions = summary.get("total_sessions", 0)
    screenshot_count = summary.get("screenshot_count", 0)

    # Build app rows
    app_rows = ""
    for i, app in enumerate(apps):
        color = generate_color(i)
        pct = app.get("percentage", 0)
        top_titles = "<br>".join(
            [f'<span class="window-title">{w["title"][:90]} ({format_duration(w["seconds"])})</span>'
             for w in app.get("top_windows", [])[:3]]
        )
        app_rows += f"""
        <tr>
            <td>
                <span class="color-dot" style="background:{color}"></span>
                <strong>{app['process']}</strong>
            </td>
            <td>{app.get('total_formatted', '0:00:00')}</td>
            <td>
                <div class="bar-container">
                    <div class="bar" style="width:{pct}%; background:{color}"></div>
                    <span class="bar-label">{pct}%</span>
                </div>
            </td>
            <td class="titles-cell">{top_titles}</td>
        </tr>"""

    # Build hourly chart bars
    hourly_bars = ""
    all_hours = sorted(hourly.keys()) if hourly else []
    max_hour_total = max(
        (sum(procs.values()) for procs in hourly.values()), default=1
    )

    for hour in all_hours:
        procs = hourly[hour]
        total = sum(procs.values())
        height_pct = (total / max_hour_total * 100) if max_hour_total > 0 else 0

        # Stack segments by process
        segments = ""
        sorted_procs = sorted(procs.items(), key=lambda x: x[1], reverse=True)
        for j, (proc, secs) in enumerate(sorted_procs):
            seg_pct = (secs / total * height_pct) if total > 0 else 0
            color = generate_color(j)
            segments += f'<div class="bar-segment" style="height:{seg_pct}%;background:{color}" title="{proc}: {format_duration(secs)}"></div>'

        hourly_bars += f"""
        <div class="hour-col">
            <div class="hour-bar" style="height:{height_pct}%">{segments}</div>
            <div class="hour-label">{hour[:2]}</div>
        </div>"""

    # Build screenshot gallery
    screenshot_gallery = ""
    for ss in screenshots:
        time_str = ss.replace("screenshot_", "").replace(".jpg", "")
        formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}" if len(time_str) >= 6 else time_str
        screenshot_gallery += f"""
        <div class="screenshot-card">
            <img src="screenshots/{ss}" alt="{ss}" loading="lazy" onclick="this.classList.toggle('expanded')">
            <div class="screenshot-time">{formatted_time}</div>
        </div>"""

    # Build timeline
    timeline_items = ""
    for item in timeline[-50:]:  # Last 50 items
        dur = format_duration(item["duration"])
        timeline_items += f"""
        <div class="timeline-item">
            <span class="timeline-time">{item['time']}</span>
            <span class="timeline-process">{item['process']}</span>
            <span class="timeline-title">{item['title']}</span>
            <span class="timeline-duration">{dur}</span>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Activity Report - {date_str}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 2rem;
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}

        /* Header */
        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: linear-gradient(135deg, #1e293b, #334155);
            border-radius: 16px;
            border: 1px solid #475569;
        }}
        .header h1 {{ font-size: 2rem; color: #f8fafc; margin-bottom: 0.5rem; }}
        .header .date {{ font-size: 1.2rem; color: #94a3b8; }}

        /* Stats Cards */
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .stat-card {{
            background: #1e293b;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            border: 1px solid #334155;
        }}
        .stat-card .value {{ font-size: 2rem; font-weight: 700; color: #60a5fa; }}
        .stat-card .label {{ font-size: 0.85rem; color: #94a3b8; margin-top: 0.25rem; }}

        /* Section */
        .section {{
            background: #1e293b;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid #334155;
        }}
        .section h2 {{
            font-size: 1.3rem;
            margin-bottom: 1rem;
            color: #f1f5f9;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        /* App Table */
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; padding: 0.75rem; color: #94a3b8; font-weight: 600; border-bottom: 1px solid #334155; font-size: 0.85rem; }}
        td {{ padding: 0.75rem; border-bottom: 1px solid #1e293b; vertical-align: top; }}
        tr:hover {{ background: #334155; }}
        .color-dot {{
            display: inline-block;
            width: 10px; height: 10px;
            border-radius: 50%;
            margin-right: 8px;
            vertical-align: middle;
        }}
        .bar-container {{
            background: #0f172a;
            border-radius: 6px;
            height: 24px;
            position: relative;
            min-width: 120px;
        }}
        .bar {{
            height: 100%;
            border-radius: 6px;
            transition: width 0.3s;
        }}
        .bar-label {{
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 0.75rem;
            color: #e2e8f0;
        }}
        .titles-cell {{ font-size: 0.8rem; color: #94a3b8; }}
        .window-title {{ display: block; margin-bottom: 2px; }}

        /* Hourly Chart */
        .hourly-chart {{
            display: flex;
            align-items: flex-end;
            gap: 4px;
            height: 200px;
            padding: 1rem 0;
        }}
        .hour-col {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 100%;
            justify-content: flex-end;
        }}
        .hour-bar {{
            width: 100%;
            border-radius: 4px 4px 0 0;
            display: flex;
            flex-direction: column-reverse;
            min-height: 2px;
        }}
        .bar-segment {{ width: 100%; min-height: 1px; }}
        .hour-label {{ font-size: 0.7rem; color: #64748b; margin-top: 4px; }}

        /* Screenshots */
        .screenshot-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1rem;
        }}
        .screenshot-card {{
            background: #0f172a;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #334155;
        }}
        .screenshot-card img {{
            width: 100%;
            display: block;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        .screenshot-card img.expanded {{
            position: fixed;
            top: 5%;
            left: 5%;
            width: 90%;
            height: 90%;
            object-fit: contain;
            z-index: 1000;
            background: rgba(0,0,0,0.9);
            border-radius: 8px;
        }}
        .screenshot-time {{
            padding: 0.5rem;
            text-align: center;
            font-size: 0.85rem;
            color: #94a3b8;
        }}

        /* Timeline */
        .timeline {{ max-height: 500px; overflow-y: auto; }}
        .timeline-item {{
            display: flex;
            gap: 1rem;
            padding: 0.4rem 0;
            border-bottom: 1px solid #1e293b;
            font-size: 0.85rem;
            align-items: center;
        }}
        .timeline-time {{ color: #64748b; font-family: monospace; min-width: 50px; }}
        .timeline-process {{
            background: #334155;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
            min-width: 120px;
            font-size: 0.8rem;
        }}
        .timeline-title {{ flex: 1; color: #94a3b8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .timeline-duration {{ color: #60a5fa; font-family: monospace; min-width: 60px; text-align: right; }}

        /* Tabs */
        .tabs {{ display: flex; gap: 0.5rem; margin-bottom: 1rem; }}
        .tab {{
            padding: 0.5rem 1rem;
            background: #334155;
            border: none;
            color: #94a3b8;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
        }}
        .tab.active {{ background: #4F46E5; color: white; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        /* Responsive */
        @media (max-width: 768px) {{
            body {{ padding: 1rem; }}
            .stats {{ grid-template-columns: repeat(2, 1fr); }}
            .screenshot-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Daily Activity Report</h1>
            <div class="date">{date_str} &middot; Generated {datetime.now().strftime('%H:%M')}</div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="value">{total_active}</div>
                <div class="label">Total Active Time</div>
            </div>
            <div class="stat-card">
                <div class="value">{len(apps)}</div>
                <div class="label">Applications Used</div>
            </div>
            <div class="stat-card">
                <div class="value">{total_sessions}</div>
                <div class="label">Window Switches</div>
            </div>
            <div class="stat-card">
                <div class="value">{screenshot_count}</div>
                <div class="label">Screenshots</div>
            </div>
        </div>

        <div class="section">
            <h2>📈 Hourly Activity</h2>
            <div class="hourly-chart">
                {hourly_bars if hourly_bars else '<p style="color:#64748b">No hourly data available yet.</p>'}
            </div>
        </div>

        <div class="section">
            <h2>🖥️ Application Usage</h2>
            <table>
                <thead>
                    <tr>
                        <th>Application</th>
                        <th>Time</th>
                        <th>Share</th>
                        <th>Top Windows</th>
                    </tr>
                </thead>
                <tbody>
                    {app_rows if app_rows else '<tr><td colspan="4" style="color:#64748b">No application data yet.</td></tr>'}
                </tbody>
            </table>
        </div>

        <div class="section">
            <div class="tabs">
                <button class="tab active" onclick="switchTab('timeline')">📋 Timeline</button>
                <button class="tab" onclick="switchTab('screenshots')">📸 Screenshots ({screenshot_count})</button>
            </div>

            <div id="tab-timeline" class="tab-content active">
                <div class="timeline">
                    {timeline_items if timeline_items else '<p style="color:#64748b">No timeline data available yet.</p>'}
                </div>
            </div>

            <div id="tab-screenshots" class="tab-content">
                <div class="screenshot-grid">
                    {screenshot_gallery if screenshot_gallery else '<p style="color:#64748b">No screenshots taken yet.</p>'}
                </div>
            </div>
        </div>
    </div>

    <script>
        function switchTab(name) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + name).classList.add('active');
            event.target.classList.add('active');
        }}

        // Close expanded screenshots on click outside
        document.addEventListener('click', function(e) {{
            if (!e.target.classList.contains('expanded')) {{
                document.querySelectorAll('img.expanded').forEach(img => img.classList.remove('expanded'));
            }}
        }});
    </script>
</body>
</html>"""

    return html


def generate_weekly_report() -> str:
    """Generate a summary report for the last 7 days."""
    today = datetime.now()
    days = []
    for i in range(6, -1, -1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        summary = load_summary(d)
        if summary:
            days.append(summary)

    if not days:
        return "<html><body><h1>No data found for the last 7 days</h1></body></html>"

    # Aggregate weekly stats
    total_seconds = sum(d.get("total_active_seconds", 0) for d in days)
    total_sessions = sum(d.get("total_sessions", 0) for d in days)
    total_screenshots = sum(d.get("screenshot_count", 0) for d in days)

    # Aggregate app usage across the week
    weekly_apps = defaultdict(float)
    for day in days:
        for app in day.get("applications", []):
            weekly_apps[app["process"]] += app.get("total_seconds", 0)

    sorted_apps = sorted(weekly_apps.items(), key=lambda x: x[1], reverse=True)

    app_rows = ""
    for i, (proc, secs) in enumerate(sorted_apps[:15]):
        color = generate_color(i)
        pct = (secs / total_seconds * 100) if total_seconds > 0 else 0
        app_rows += f"""
        <tr>
            <td><span class="color-dot" style="background:{color}"></span><strong>{proc}</strong></td>
            <td>{format_duration(secs)}</td>
            <td>
                <div class="bar-container">
                    <div class="bar" style="width:{pct}%; background:{color}"></div>
                    <span class="bar-label">{pct:.1f}%</span>
                </div>
            </td>
        </tr>"""

    # Daily bars
    daily_bars = ""
    max_daily = max((d.get("total_active_seconds", 0) for d in days), default=1)
    for day in days:
        secs = day.get("total_active_seconds", 0)
        height_pct = (secs / max_daily * 100) if max_daily > 0 else 0
        date_label = day["date"][5:]  # MM-DD
        daily_bars += f"""
        <div class="hour-col">
            <div class="hour-bar" style="height:{height_pct}%">
                <div class="bar-segment" style="height:100%;background:#4F46E5" title="{format_duration(secs)}"></div>
            </div>
            <div class="hour-label">{date_label}</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Weekly Activity Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 2rem; padding: 2rem; background: linear-gradient(135deg, #1e293b, #334155); border-radius: 16px; border: 1px solid #475569; }}
        .header h1 {{ font-size: 2rem; color: #f8fafc; margin-bottom: 0.5rem; }}
        .header .date {{ font-size: 1.2rem; color: #94a3b8; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .stat-card {{ background: #1e293b; border-radius: 12px; padding: 1.5rem; text-align: center; border: 1px solid #334155; }}
        .stat-card .value {{ font-size: 2rem; font-weight: 700; color: #60a5fa; }}
        .stat-card .label {{ font-size: 0.85rem; color: #94a3b8; margin-top: 0.25rem; }}
        .section {{ background: #1e293b; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; border: 1px solid #334155; }}
        .section h2 {{ font-size: 1.3rem; margin-bottom: 1rem; color: #f1f5f9; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; padding: 0.75rem; color: #94a3b8; font-weight: 600; border-bottom: 1px solid #334155; font-size: 0.85rem; }}
        td {{ padding: 0.75rem; border-bottom: 1px solid #1e293b; }}
        tr:hover {{ background: #334155; }}
        .color-dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; vertical-align: middle; }}
        .bar-container {{ background: #0f172a; border-radius: 6px; height: 24px; position: relative; min-width: 120px; }}
        .bar {{ height: 100%; border-radius: 6px; }}
        .bar-label {{ position: absolute; right: 8px; top: 50%; transform: translateY(-50%); font-size: 0.75rem; color: #e2e8f0; }}
        .hourly-chart {{ display: flex; align-items: flex-end; gap: 8px; height: 200px; padding: 1rem 0; }}
        .hour-col {{ flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; }}
        .hour-bar {{ width: 100%; border-radius: 4px 4px 0 0; display: flex; flex-direction: column-reverse; min-height: 2px; }}
        .bar-segment {{ width: 100%; min-height: 1px; }}
        .hour-label {{ font-size: 0.75rem; color: #64748b; margin-top: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Weekly Activity Report</h1>
            <div class="date">Last 7 Days &middot; {days[0]['date']} to {days[-1]['date']}</div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="value">{format_duration(total_seconds)}</div>
                <div class="label">Total Active Time</div>
            </div>
            <div class="stat-card">
                <div class="value">{len(days)}</div>
                <div class="label">Days Tracked</div>
            </div>
            <div class="stat-card">
                <div class="value">{total_sessions}</div>
                <div class="label">Window Switches</div>
            </div>
            <div class="stat-card">
                <div class="value">{total_screenshots}</div>
                <div class="label">Screenshots</div>
            </div>
        </div>

        <div class="section">
            <h2>📅 Daily Activity</h2>
            <div class="hourly-chart">{daily_bars}</div>
        </div>

        <div class="section">
            <h2>🖥️ Top Applications (Week)</h2>
            <table>
                <thead><tr><th>Application</th><th>Total Time</th><th>Share</th></tr></thead>
                <tbody>{app_rows}</tbody>
            </table>
        </div>
    </div>
</body>
</html>"""

    return html


def main():
    """Main entry point for report generation."""
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--week":
            html = generate_weekly_report()
            report_path = DATA_DIR / "weekly-report.html"
        else:
            html = generate_html_report(arg)
            report_path = DATA_DIR / arg / "report.html"
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        html = generate_html_report(today)
        report_path = DATA_DIR / today / "report.html"

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Report generated: {report_path}")

    # Open in browser
    webbrowser.open(str(report_path))


if __name__ == "__main__":
    main()
