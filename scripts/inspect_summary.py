import pypdf

reader = pypdf.PdfReader("data/reports/edition_2/UNDP-_Arabic_Localization_Summary_Report_OECD_9-3-2025_Final__838.pdf")
print(f"Total pages: {len(reader.pages)}")
for i, page in enumerate(reader.pages):
    txt = page.extract_text() or ""
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    first_few = " | ".join(lines[:4])
    print(f"Page {i+1}: length={len(txt)} chars | preview: {first_few[:120]}")
