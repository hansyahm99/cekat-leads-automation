import pandas as pd
from pathlib import Path
from glob import glob

def get_latest_bronze_file():
    files = glob("data/bronze/leads_*.csv")
    return max(files, key=lambda f: Path(f).stat().st_mtime)

def clean():
    latest_file = get_latest_bronze_file()
    df = pd.read_csv(latest_file)

    df = df.drop_duplicates()
    df = df.dropna(how="all")

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    label_column = [
        "label_cold", "label_warm", "label_hot",
        "spam", "out_of_area", "remarketing", "no_response"
    ]

    for col in label_column:
        if col in df.columns:
            df[col] = df[col].notna() & (df[col].astype(str).str.strip() != "")

    silver_dir = Path("data/silver")
    silver_dir.mkdir(parents=True, exist_ok=True)
    output_path = silver_dir / Path(latest_file).name.replace("leads_", "leads_cleaned_")
    df.to_csv(output_path, index=False)

    print(f"Wrote {len(df)} cleaned rows to {output_path}")

if __name__ == "__main__":
    clean()