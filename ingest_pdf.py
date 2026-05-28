"""
Legacy ingest script retained for compatibility.

The app now uses direct file-based retrieval (no vector DB ingestion needed).
"""
import os
from pypdf import PdfReader

PDF_PATH = os.path.join("data", "telecom_guide.pdf")


def main() -> None:
    if not os.path.exists(PDF_PATH):
        print(f"Missing file: {PDF_PATH}")
        return
    reader = PdfReader(PDF_PATH)
    print(f"Guide data is ready: {len(reader.pages)} pages found in {PDF_PATH}.")
    print("No ingestion step is required.")


if __name__ == "__main__":
    main()
