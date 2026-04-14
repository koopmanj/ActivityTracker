# Weekly Work Report — Reusable Generation Prompt

Use this prompt with your ActivityTracker data to generate a comprehensive weekly work report. Attach the `summary.json` files for each day of the target week, or paste the contents inline.

---

## Prompt

```
You are generating a weekly work report from ActivityTracker data (summary.json files for each day). Analyze the provided data and produce a comprehensive markdown report.

## Author Context

Customize this section with your own details before using the prompt:

- **Name:** Your Name
- **Role:** Your Role, Your Organization
- **Primary tools:** (list the applications you use daily, e.g., Microsoft Teams, VS Code, Chrome/Edge, PowerPoint, Excel)

## Data Input Format

Each day's `summary.json` contains:
- `date` — YYYY-MM-DD
- `total_active_seconds` / `total_active_formatted` — total tracked foreground time
- `total_sessions` — number of window switches
- `applications[]` — array of apps used, each with:
  - `process` — executable name (ms-teams.exe, Code.exe, chrome.exe, msedge.exe, POWERPNT.EXE, EXCEL.EXE, draw.io.exe, etc.)
  - `total_seconds` / `total_formatted` — time spent
  - `percentage` — share of total
  - `top_windows[]` — array of { title, seconds } for the most-used window titles

## How to Extract Information from Window Titles

### Microsoft Teams (`ms-teams.exe`)
- **1:1 chats:** `"Chat | LastName, FirstName | Organization | user@domain.com | Microsoft Teams"`
- **Group chats:** `"Chat | Person1, Person2, Person3, +N | Organization | ..."` or `"Chat | [Channel Name] | Organization | ..."`
- **Named group chats:** `"[TICKET-ID] - [Topic Name] | ..."` or `"Chat Topic Name | ..."`
- **Meetings/Calls:** `"MeetingName | Organization | ..."` — longer-duration entries without "Chat |" prefix
- **Extract:** participant names, meeting names, chat channel names. Estimate meeting duration from active window seconds (actual call time is typically longer).

### Confluence / Jira (via `msedge.exe` or `chrome.exe`)
- **Confluence edit:** `"Edit - PageTitle - SpaceName - Confluence and X more pages - Work - Microsoft Edge"`
- **Confluence view:** `"PageTitle - SpaceName - Confluence and X more pages - Work - Microsoft Edge"`
- **Jira:** `"[TICKET-123] Title - Jira and X more pages - Work - Microsoft Edge"`
- **Extract:** page names, space names, ticket IDs, whether editing or viewing.

### Claude AI Research (`chrome.exe`)
- **Pattern:** `"SessionTitle - Claude - Google Chrome"` (e.g., "Research topic - Claude")
- **Extract:** research topic, duration spent. Group as AI/research activity.

### VS Code (`Code.exe`)
- **Pattern:** `"filename - workspace - Visual Studio Code"` (e.g., "main.py - my-project - Visual Studio Code")
- **Extract:** filename, workspace/project name. Group by project.

### PowerPoint (`POWERPNT.EXE`)
- **Pattern:** `"filename.pptx - PowerPoint"` or slide show mode
- **Extract:** presentation filename, whether editing or presenting.

### Excel (`EXCEL.EXE`)
- **Pattern:** `"filename.xlsx - Excel"`
- **Extract:** spreadsheet filename.

### draw.io (`draw.io.exe`)
- **Pattern:** `"filename.drawio - draw.io"`
- **Extract:** diagram filename.

### Word (`WINWORD.EXE`)
- **Pattern:** `"filename.docx - Word"` (may include "Protected View" or "Read-Only")
- **Extract:** document filename.

### Microsoft 365 Copilot (`M365Copilot.exe`)
- Always `"Microsoft 365 Copilot"` — track total usage time.

### Ignore / Filter Out
- `LockApp.exe` (Windows lock screen) — subtract from active time
- `explorer.exe` with "Task Switching" — window switching overhead
- `unknown` / "No Active Window" — idle/screensaver
- `SearchHost.exe`, `ShellExperienceHost.exe` — system processes
- `ScreenClippingHost.exe` — screenshot utility (brief usage)

## Work Stream Classification

Classify all activities into work streams based on keywords in window titles. Define your own work streams below. Example structure:

### Example Work Stream
**Keywords:** keyword1, keyword2, keyword3
**Includes:** Meetings, documents, diagrams, research sessions related to this topic

(Repeat for each work stream relevant to your role. Order by importance.)

### Administrative
**Keywords:** invoice, outlook, calendar, expense
**Includes:** Email handling, calendar management, administrative tasks. Only include if significant time spent.

## Output Format

Generate this exact markdown structure:

```markdown
# Weekly Work Report — W{WEEK_NUMBER} ({MONTH} {START_DAY}–{END_DAY}, {YEAR})

**Author:** {Name} — {Role}, {Organization}
**Period:** {DayOfWeek} {StartDate} – {DayOfWeek} {EndDate} {Year}
**Total Tracked Active Time:** ~{HOURS}h {MINUTES}m across {N} active days

---

## Executive Summary

{2-4 sentence paragraph summarizing the week's dominant themes. Name the top 3 work streams. Mention key meetings, deliverables, and any notable events. Be specific — reference actual meeting names, document names, and stakeholders.}

---

## Key Accomplishments by Work Stream

### {Work Stream Name}

**Objective:** {One sentence describing the strategic objective.}

{For each significant activity in this work stream:}
- **{Activity Name}:** {Description of what was done} — {duration or context}.

**Deliverables:**
- {Artifact name} ({format/type})
- ...

{Repeat for each active work stream this week. Only include work streams that had meaningful activity. Order by time invested (largest first).}

---

## Key Meetings & Stakeholder Engagement

| Stakeholder / Meeting | Topic | Day |
|---|---|---|
| **{Meeting or Person Name}** | {Topic} | {Day abbreviation} |
| ... | ... | ... |

{Include all meetings, calls, and significant 1:1 chats. Sort roughly by day.}

---

## Artifacts Delivered

| Artifact | Format | Location |
|---|---|---|
| {Artifact name} | {PowerPoint/Excel/draw.io/Markdown/Confluence/etc.} | {Filename or location} |
| ... | ... | ... |

{List all documents, diagrams, presentations, and code artifacts that were created or significantly updated.}

---

## Time Investment Analysis

| Category | Hours | % of Week |
|---|---|---|
| {Work Stream} | ~{X}h {Y}m | {Z}% |
| ... | ... | ... |

{Sum should approximate total tracked time. Round to nearest 15 minutes.}

---

## Next Week Outlook & Open Items

### Priorities
1. {Priority item based on this week's momentum and open threads}
2. ...

### Open Threads
- {Thread} — {brief status}
- ...

### Upcoming Meetings
- {Meeting name or stakeholder alignment}
- ...

---

*Report generated from ActivityTracker data on {GENERATION_DATE}. Active time represents tracked foreground window usage and may undercount time spent in meetings, phone calls, or whiteboard sessions not captured by window tracking.*
```

## Important Rules

1. **Be specific, not generic.** Use actual document names, meeting names, and stakeholder names from the data.
2. **Estimate durations conservatively.** Window active time undercounts meeting time (you might look at Teams for 5 minutes during a 30-minute call). Note this where relevant.
3. **Cross-reference across days.** If the same document or topic appears on multiple days, consolidate into one bullet with "across Mon–Thu" rather than listing separately.
4. **Filter noise.** Don't report on system processes, brief (<10 second) window switches, or lock screen time.
5. **Weekend work.** If Saturday/Sunday has activity, include it but note it as weekend work.
6. **Personal items.** Briefly note personal admin only if it impacted work time significantly. Keep private details minimal.
7. **Executive summary first.** Write the executive summary AFTER analyzing all the data, so it accurately reflects the week's key themes.
8. **Time percentages must add up.** The time investment table should account for ~90-100% of total tracked time.
9. **Deliverables = tangible outputs.** Only list artifacts that were created or significantly updated, not things merely viewed.

## Attach Your Data Below

Paste or attach the `summary.json` contents for each day of the target week:

{PASTE summary.json FILES HERE — one per day}
```

---

## Quick Usage Guide

1. **Start of week:** Copy the prompt above
2. **Customize:** Fill in the Author Context and Work Stream Classification sections with your own details
3. **Gather data:** Go to `data/` and find the daily directories for the target week (e.g., `2026-04-07/`, `2026-04-08/`, etc.)
4. **Attach data:** Paste the contents of each day's `summary.json` after the prompt
5. **Optional enrichment:** For richer meeting/chat detail, also paste the `activity.jsonl` files (these contain the full timeline of window switches)
6. **Generate:** Submit to Claude or another AI assistant and review the output
7. **Save:** Save as `report/weekly-work-report-2026-W{XX}.md`

### Collecting Data (PowerShell)
```powershell
# Collect all summary.json files for a given week (Mon-Fri)
$weekStart = "2026-04-07"
$dates = 0..4 | ForEach-Object { (Get-Date $weekStart).AddDays($_).ToString("yyyy-MM-dd") }
$dates | ForEach-Object {
    $file = "data/$_/summary.json"
    if (Test-Path $file) {
        Write-Host "`n=== $_ ===" -ForegroundColor Cyan
        Get-Content $file
    }
}
```
