import os
import re
import json
import pypdf

MANIFEST_PATH = "data/download_manifest.json"
CHUNKS_PATH = "data/processed/chunks.json"
INDICATORS_PATH = "data/processed/indicators_db.json"
INGESTION_REPORT_PATH = "data/ingestion_report.json"

SDG_DEFINITIONS = [
    {"num": 1, "ar": "القضاء على الفقر", "en": "No Poverty"},
    {"num": 2, "ar": "القضاء التام على الجوع", "en": "Zero Hunger"},
    {"num": 3, "ar": "الصحة الجيدة والرفاه", "en": "Good Health and Well-being"},
    {"num": 4, "ar": "التعليم الجيد", "en": "Quality Education"},
    {"num": 5, "ar": "المساواة بين الجنسين", "en": "Gender Equality"},
    {"num": 6, "ar": "المياه النظيفة والنظافة الصحية", "en": "Clean Water and Sanitation"},
    {"num": 7, "ar": "طاقة نظيفة وبأسعار معقولة", "en": "Affordable and Clean Energy"},
    {"num": 8, "ar": "العمل اللائق ونمو الاقتصاد", "en": "Decent Work and Economic Growth"},
    {"num": 9, "ar": "الصناعة والابتكار والهياكل الأساسية", "en": "Industry, Innovation and Infrastructure"},
    {"num": 10, "ar": "الحد من أوجه عدم المساواة", "en": "Reduced Inequalities"},
    {"num": 11, "ar": "مدن ومجتمعات محلية مستدامة", "en": "Sustainable Cities and Communities"},
    {"num": 12, "ar": "الاستهلاك والإنتاج المسؤولان", "en": "Responsible Consumption and Production"},
    {"num": 13, "ar": "العمل المناخي", "en": "Climate Action"},
    {"num": 14, "ar": "الحياة تحت الماء", "en": "Life Below Water"},
    {"num": 15, "ar": "الحياة في البر", "en": "Life on Land"},
    {"num": 16, "ar": "السلام والعدل والمؤسسات القوية", "en": "Peace, Justice and Strong Institutions"},
    {"num": 17, "ar": "عقد الشراكات لتحقيق الأهداف", "en": "Partnerships for the Goals"}
]

def detect_sdgs(text):
    found = []
    text_lower = text.lower()
    for sdg in SDG_DEFINITIONS:
        # Check Arabic name
        words = sdg["ar"].split()
        if sdg["ar"] in text or (len(words) >= 2 and all(w in text for w in words)):
            found.append(sdg["num"])
            continue
        # Check goal number e.g. الهدف الأول, الهدف 1, SDG 1
        patterns = [
            rf"sdg\s*{sdg['num']}\b",
            rf"الهدف\s*(رقم\s*)?{sdg['num']}\b"
        ]
        num_ar_map = {
            1: "الأول", 2: "الثاني", 3: "الثالث", 4: "الرابع", 5: "الخامس",
            6: "السادس", 7: "السابع", 8: "الثامن", 9: "التاسع", 10: "العاشر",
            11: "الحادي عشر", 12: "الثاني عشر", 13: "الثالث عشر", 14: "الرابع عشر",
            15: "الخامس عشر", 16: "السادس عشر", 17: "السابع عشر"
        }
        if sdg["num"] in num_ar_map:
            patterns.append(rf"الهدف\s+{num_ar_map[sdg['num']]}")
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                found.append(sdg["num"])
                break
    return sorted(list(set(found)))

def clean_arabic_text(text):
    if not text:
        return ""
    # Normalize unicode whitespace
    text = re.sub(r'[\r\t\f\v]', ' ', text)
    # Remove multiple spaces
    text = re.sub(r' +', ' ', text)
    # Remove repeated blank lines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def process_all_reports():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    os.makedirs("data/processed", exist_ok=True)
    
    all_chunks = []
    report_stats = []
    total_pages = 0
    total_chunks = 0
    
    print(f"Starting processing of {len(manifest)} reports...")
    
    for idx, item in enumerate(manifest):
        path = item["path"]
        edition = item["edition"]
        gov_ar = item["governorate_ar"]
        gov_en = item["governorate_en"]
        gov_id = item["governorate_id"]
        is_summary = item["is_summary"]
        fname = item["filename"]
        source_url = item["url"]
        
        stat = {
            "index": idx + 1,
            "filename": fname,
            "edition": edition,
            "governorate_ar": gov_ar,
            "governorate_en": gov_en,
            "governorate_id": gov_id,
            "is_summary": is_summary,
            "source_url": source_url,
            "status": "success",
            "page_count": 0,
            "extracted_chars": 0,
            "chunks_count": 0,
            "error": None
        }
        
        if not os.path.exists(path):
            stat["status"] = "missing_file"
            stat["error"] = "File not found on disk"
            report_stats.append(stat)
            continue
            
        try:
            reader = pypdf.PdfReader(path)
            num_pages = len(reader.pages)
            stat["page_count"] = num_pages
            total_pages += num_pages
            
            doc_chars = 0
            
            for p_num in range(num_pages):
                page = reader.pages[p_num]
                raw_text = page.extract_text() or ""
                clean_txt = clean_arabic_text(raw_text)
                doc_chars += len(clean_txt)
                
                if len(clean_txt) < 15:
                    continue
                    
                sdgs = detect_sdgs(clean_txt)
                
                # Create structured chunk
                chunk_id = f"e{edition}_{gov_id}_p{p_num + 1}"
                chunk = {
                    "id": chunk_id,
                    "edition": edition,
                    "edition_name": "الإصدار الأول (2021)" if edition == 1 else "الإصدار الثاني (2024/2025)",
                    "governorate_ar": gov_ar,
                    "governorate_en": gov_en,
                    "governorate_id": gov_id,
                    "is_summary": is_summary,
                    "page_number": p_num + 1,
                    "total_pages": num_pages,
                    "filename": fname,
                    "source_url": source_url,
                    "sdg_numbers": sdgs,
                    "char_count": len(clean_txt),
                    "text": clean_txt
                }
                all_chunks.append(chunk)
                
            stat["extracted_chars"] = doc_chars
            stat["chunks_count"] = len([c for c in all_chunks if c["filename"] == fname])
            total_chunks += stat["chunks_count"]
            print(f"[{idx+1}/{len(manifest)}] OK: E{edition} {gov_ar} ({num_pages} pages, {stat['chunks_count']} chunks)")
            
        except Exception as e:
            stat["status"] = "extraction_error"
            stat["error"] = str(e)
            print(f"[{idx+1}/{len(manifest)}] ERROR in {fname}: {e}")
            
        report_stats.append(stat)
        
    print(f"\nExtraction complete! Total pages: {total_pages}, Total chunks: {len(all_chunks)}")
    
    # Save chunks
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
        
    # Ingestion report
    ingestion_report = {
        "summary": {
            "total_reports": len(manifest),
            "successfully_processed": sum(1 for s in report_stats if s["status"] == "success"),
            "failed_reports": sum(1 for s in report_stats if s["status"] != "success"),
            "edition_1_reports": sum(1 for s in report_stats if s["edition"] == 1),
            "edition_2_reports": sum(1 for s in report_stats if s["edition"] == 2),
            "total_pages_indexed": total_pages,
            "total_chunks_created": len(all_chunks)
        },
        "reports": report_stats
    }
    
    with open(INGESTION_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(ingestion_report, f, ensure_ascii=False, indent=2)
        
    print(f"Saved chunks to {CHUNKS_PATH}")
    print(f"Saved ingestion report to {INGESTION_REPORT_PATH}")

if __name__ == "__main__":
    process_all_reports()
