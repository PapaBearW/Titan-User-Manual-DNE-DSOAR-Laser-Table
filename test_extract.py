import pdfplumber
from pathlib import Path

base = Path(".")
for pdf in base.glob("*.pdf"):
    print(f"\n=== {pdf.name} ===")
    with pdfplumber.open(pdf) as p:
        total_pages = len(p.pages)
        sample_text = ""
        focus_count = 0
        for page in p.pages:
            t = page.extract_text() or ""
            focus_count += t.lower().count("focus")
            if not sample_text and t.strip():
                sample_text = t[:200]
        print(f"Pages: {total_pages}")
        print(f"'focus' occurrences: {focus_count}")
        if sample_text:
            print(f"Sample text: {sample_text}")
        else:
            print("NO TEXT EXTRACTED - this is likely a scanned image PDF (needs OCR)")
