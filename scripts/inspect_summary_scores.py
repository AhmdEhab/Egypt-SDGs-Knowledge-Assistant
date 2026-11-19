import pypdf

reader = pypdf.PdfReader("data/reports/edition_2/UNDP-_Arabic_Localization_Summary_Report_OECD_9-3-2025_Final__838.pdf")
for p in [4, 5, 6, 7]:
    print(f"\n================ Summary Report Page {p} ================")
    txt = reader.pages[p-1].extract_text()
    print(txt[:2000])
