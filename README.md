# Daily Leads Report Automation

Portfolio project: a batch ETL pipeline that automates the daily leads report from Cekat.AI CRM — replacing a manual process that previously took up to 30 minutes every morning.

## Background

Every day at 9am, someone needs to manually pull data from the Cekat CRM Tracker to check total leads from the start of the month through the previous day — including a breakdown by label (Hot/Warm/Cold), booking count, spam, no response, out of area, and show/no-show status. This project automates that entire process so it runs on its own, with no manual intervention.

## Pipeline Flow

```
GitHub Actions (cron, daily at 09:00 WIB)
      │
      ▼
🥉 BRONZE — scrape_cekat.py
   Selenium logs into chat.cekat.ai, scrapes the CRM Tracker
   (headers + rows captured in one atomic JavaScript call,
   avoiding StaleElementReferenceException)
   → data/bronze/leads_YYYYMMDD.csv
      │
      ▼
🥈 SILVER — clean.py
   Drop duplicates, standardize column names,
   convert label columns (Hot/Warm/Cold/Spam/etc.) to boolean
   → data/silver/leads_cleaned_YYYYMMDD.csv
      │
      ▼
🥇 GOLD — aggregate.py
   Compute business metrics: total leads, per-label breakdown,
   show count, booking count
   → data/gold/daily_summary_YYYYMMDD.csv
      │
      ▼
load_to_sqlite.py
   Appends the day's summary into a SQLite database,
   building a historical time series automatically
   → db/leads_report.db
      │
      ▼
GitHub Actions commits the db back to the repo
   (persistent across runs, audit trail via git history)
```

## Architecture

| Aspect | Choice | Reason |
|---|---|---|
| Processing paradigm | **Batch**, not streaming | Business need is a daily report, not real-time |
| Data flow | **ETL** (medallion: bronze-silver-gold) | Transform happens in stages before landing in final storage |
| Orchestrator | **GitHub Actions** (cron), not Airflow | Small scale, no need for an always-on scheduler |
| Storage | **SQLite** | Free forever, no risk of a cloud trial expiring |
| Scraping | **Selenium**, not an API | Cekat.AI has no export API for CRM Tracker data |

## Project Structure

```
cekat-leads-automation/
├── .github/
│   └── workflows/
│       └── daily_report.yml
├── scripts/
│   ├── scrape_cekat.py       (bronze)
│   ├── clean.py               (silver)
│   ├── aggregate.py           (gold)
│   └── load_to_sqlite.py
├── data/
│   ├── bronze/                (gitignored, transient)
│   ├── silver/                (gitignored, transient)
│   └── gold/                  (gitignored, transient)
├── db/
│   └── leads_report.db        (committed on every run)
├── .env                        (local only, gitignored)
├── .gitignore
├── requirements.txt
└── README.md
```

## Key Column Definitions

- **`label_hot` / `label_warm` / `label_cold`** — filled with a date if the lead was ever marked with that status; empty otherwise
- **`book`** — always filled with a date/time once the agent follows up and schedules a booking; not an indicator of a confirmed booking
- **`visit`** — filled only when the customer has actually shown up (confirmed attendance), not just a scheduled date

## How to Run

### Local Setup (development & testing)

```bash
git clone https://github.com/hansyahm99/cekat-leads-automation.git
cd cekat-leads-automation
pip install -r requirements.txt
```

Create a `.env` file in the root:
```
CEKAT_EMAIL=your_login_email
CEKAT_PASSWORD=your_password
```

Run the pipeline in order:
```bash
python scripts/scrape_cekat.py
python scripts/clean.py
python scripts/aggregate.py
python scripts/load_to_sqlite.py
```

### Production (automated via GitHub Actions)

1. Push the repo to GitHub
2. Add **GitHub Secrets**: `CEKAT_EMAIL`, `CEKAT_PASSWORD`
   (Settings → Secrets and variables → Actions)
3. Enable **write permission** for Actions:
   Settings → Actions → General → Workflow permissions → **Read and write permissions**
4. The workflow runs automatically every day at 09:00 WIB (cron `0 2 * * *` UTC), or can be triggered manually from the **Actions → Run workflow** tab

## Viewing the Data

```bash
python -c "
import sqlite3
import pandas as pd
conn = sqlite3.connect('db/leads_report.db')
print(pd.read_sql('SELECT * FROM daily_leads_summary', conn))
"
```

## Troubleshooting Encountered

| Issue | Cause | Fix |
|---|---|---|
| `WinError 193: not a valid Win32 application` | `webdriver-manager` resolved the wrong ChromeDriver path on Windows | Use a manual path to `chromedriver.exe` for local testing; on GitHub Actions (Ubuntu), Selenium 4.18+'s auto-detect works fine without a manual path |
| `StaleElementReferenceException` | The CRM Tracker page re-renders (React) mid-scrape when reading elements one by one | Fetch the entire table in a single `driver.execute_script()` call (atomic), instead of looping through elements with Selenium |
| Login timeout despite correct credentials | The login process took longer than the 20-second wait | Extended `WebDriverWait` to 40 seconds |
| `TypeError: 'NoneType' object is not iterable` on `send_keys()` | Environment variable not read correctly (typo in `.env`, e.g. `PASSSWORD` instead of `PASSWORD`) | Make sure the variable name in `.env` matches exactly what's passed to `os.getenv()` |
| `By.NAME` selector failed to find the element | Cekat's input fields have no `name`/`id` attribute | Use `By.CSS_SELECTOR` based on the `type` attribute instead (`input[type='email']`) |
| `git push` failed with 403 in GitHub Actions | Default `GITHUB_TOKEN` is read-only | Settings → Actions → General → Workflow permissions → **Read and write permissions** |
| `table has no column named X` when loading to SQLite | The SQLite table schema doesn't auto-update when a new column is added in the script | Delete the old database to let the schema recreate (safe only during development) |
