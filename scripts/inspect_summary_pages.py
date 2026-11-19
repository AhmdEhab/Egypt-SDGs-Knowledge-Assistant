import pypdf

reader = pypdf.PdfReader("data/reports/edition_2/UNDP-_Arabic_Localization_Summary_Report_OECD_9-3-2025_Final__838.pdf")
for page_num in [2, 3, 16, 17]:
    print(f"\n================ PAGE {page_num} ================")
    print(reader.pages[page_num - 1].extract_text()[:3000])
