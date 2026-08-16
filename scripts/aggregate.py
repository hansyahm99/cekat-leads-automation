import pandas as pd
from pathlib import Path
from glob import glob
from datetime import datetime


def get_latest_silver_file():
    files = glob("data/silver/leads_cleaned_*.csv")
    return max(files, key=lambda f: Path(f).stat().st_mtime)


def aggregate():
    latest_file = get_latest_silver_file()
    df = pd.read_csv(latest_file)

    summary = {
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "total_leads": len(df),
        "hot_leads": int(df["label_hot"].sum()) if "label_hot" in df.columns else 0,
        "warm_leads": int(df["label_warm"].sum()) if "label_warm" in df.columns else 0,
        "cold_leads": int(df["label_cold"].sum()) if "label_cold" in df.columns else 0,
        "spam": int(df["spam"].sum()) if "spam" in df.columns else 0,
        "out_of_area": int(df["out_of_area"].sum()) if "out_of_area" in df.columns else 0,
        "no_response": int(df["no_response"].sum()) if "no_response" in df.columns else 0,
        "show_count": int(df["visit"].notna().sum()) if "visit" in df.columns else 0,
        "unconfirmed_count": int(df["visit"].isna().sum()) if "visit" in df.columns else 0,
        "booking_count": int(df["book"].notna().sum()) if "book" in df.columns else 0,
    }

    gold_dir = Path("data/gold")
    gold_dir.mkdir(parents=True, exist_ok=True)
    output_path = gold_dir / f"daily_summary_{datetime.now().strftime('%Y%m%d')}.csv"

    pd.DataFrame([summary]).to_csv(output_path, index=False)
    print(f"Wrote summary to {output_path}")


if __name__ == "__main__":
    aggregate()