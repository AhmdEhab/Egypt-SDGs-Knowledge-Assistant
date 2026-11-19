import pypdf

def dump_pages(path, max_p=8):
    print(f"\n==================== {path} ====================")
    reader = pypdf.PdfReader(path)
    print(f"Total pages: {len(reader.pages)}")
    for i in range(min(max_p, len(reader.pages))):
        print(f"\n--- Page {i+1} ---")
        txt = reader.pages[i].extract_text() or ""
        print(txt[:1500])

if __name__ == "__main__":
    dump_pages("data/reports/edition_1/9_الغربية.pdf", 6)
    dump_pages("data/reports/edition_2/10_UNDP___Gharbia_Report_21-11-2024_compressed_0d5.pdf", 6)
