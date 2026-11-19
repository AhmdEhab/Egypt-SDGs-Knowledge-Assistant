import pypdf

reader = pypdf.PdfReader("data/reports/edition_1/9_الغربية.pdf")
print("Total pages in Edition 1 Gharbia:", len(reader.pages))
for p in [4, 5, 6, 7, 8, 9, 10, 20, 24, 25]:
    if p <= len(reader.pages):
        print(f"\n--- Page {p} ---")
        print(reader.pages[p-1].extract_text()[:600])
