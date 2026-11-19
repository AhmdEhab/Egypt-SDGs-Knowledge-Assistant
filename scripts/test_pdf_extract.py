import os
import pypdf

def inspect_pdf(path):
    print(f"\n--- Inspecting {path} ---")
    reader = pypdf.PdfReader(path)
    print(f"Num pages: {len(reader.pages)}")
    for i in range(min(5, len(reader.pages))):
        text = reader.pages[i].extract_text() or ""
        print(f"Page {i+1} preview ({len(text)} chars): {text[:200]}...")

if __name__ == "__main__":
    # Test summary report
    summary_path = "data/reports/edition_2/UNDP-_Arabic_Localization_Summary_Report_OECD_9-3-2025_Final__838.pdf"
    if os.path.exists(summary_path):
        inspect_pdf(summary_path)
        
    # Test Edition 1 Cairo
    cairo_e1 = "data/reports/edition_1/6_القاهرة.pdf"
    if os.path.exists(cairo_e1):
        inspect_pdf(cairo_e1)
        
    # Test Edition 2 Cairo
    cairo_e2 = "data/reports/edition_2/1_UNDP___Cairo_Report_19-11-2024_compressed_b4c.pdf"
    if os.path.exists(cairo_e2):
        inspect_pdf(cairo_e2)
