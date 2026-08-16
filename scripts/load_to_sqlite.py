import sqlite3
import pandas as pd
from pathlib import Path
from glob import glob


def get_latest_gold_file():
    files = glob("data/gold/daily_summary_*.csv")
    return max(files, key=lambda f: Path(f).stat().st_mtime)


def load():
    latest_file = get_latest_gold_file()
    df = pd.read_csv(latest_file)

    db_dir = Path("db")
    db_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_dir / "leads_report.db")

    df.to_sql("daily_leads_summary", conn, if_exists="append", index=False)
    conn.close()

    print(f"Loaded {len(df)} row(s) into db/leads_report.db")


if __name__ == "__main__":
    load()