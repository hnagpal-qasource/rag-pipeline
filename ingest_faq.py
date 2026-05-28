"""
Legacy ingest script retained for compatibility.

The app now uses direct file-based retrieval (no vector DB ingestion needed).
"""
import os
import pandas as pd

CSV_PATH = os.path.join("data", "faq.csv")


def main() -> None:
    if not os.path.exists(CSV_PATH):
        print(f"Missing file: {CSV_PATH}")
        return
    df = pd.read_csv(CSV_PATH)
    print(f"FAQ data is ready: {len(df)} rows found in {CSV_PATH}.")
    print("No ingestion step is required.")


if __name__ == "__main__":
    main()
