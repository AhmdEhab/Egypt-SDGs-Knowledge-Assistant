import os
import re
import json
import time
import requests
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*"
}

E1_DIR = "data/reports/edition_1"
E2_DIR = "data/reports/edition_2"

# Mapping governorate names (Arabic / English / transliteration)
GOVERNORATES = [
    {"ar": "القاهرة", "en": "Cairo", "id": "cairo"},
    {"ar": "الإسكندرية", "en": "Alexandria", "id": "alexandria"},
    {"ar": "بورسعيد", "en": "Port Said", "id": "portsaid"},
    {"ar": "السويس", "en": "Suez", "id": "suez"},
    {"ar": "دمياط", "en": "Damietta", "id": "damietta"},
    {"ar": "الدقهلية", "en": "Dakahlia", "id": "dakahlia"},
    {"ar": "الشرقية", "en": "Sharkia", "id": "sharkia"},
    {"ar": "القليوبية", "en": "Qalyubia", "id": "qalyubia"},
    {"ar": "كفر الشيخ", "en": "Kafr El-Sheikh", "id": "kafr_elsheikh"},
    {"ar": "الغربية", "en": "Gharbia", "id": "gharbia"},
    {"ar": "المنوفية", "en": "Menofia", "id": "menofia"},
    {"ar": "البحيرة", "en": "Beheira", "id": "beheira"},
    {"ar": "الإسماعيلية", "en": "Ismailia", "id": "ismailia"},
    {"ar": "الجيزة", "en": "Giza", "id": "giza"},
    {"ar": "بني سويف", "en": "Beni Suef", "id": "beni_suef"},
    {"ar": "الفيوم", "en": "Faiyum", "id": "faiyum"},
    {"ar": "المنيا", "en": "Minya", "id": "minya"},
    {"ar": "أسيوط", "en": "Assiut", "id": "assiut"},
    {"ar": "سوهاج", "en": "Sohag", "id": "sohag"},
    {"ar": "قنا", "en": "Qena", "id": "qena"},
    {"ar": "الأقصر", "en": "Luxor", "id": "luxor"},
    {"ar": "أسوان", "en": "Aswan", "id": "aswan"},
    {"ar": "البحر الأحمر", "en": "Red Sea", "id": "red_sea"},
    {"ar": "الوادي الجديد", "en": "New Valley", "id": "new_valley"},
    {"ar": "مطروح", "en": "Matrouh", "id": "matrouh"},
    {"ar": "شمال سيناء", "en": "North Sinai", "id": "north_sinai"},
    {"ar": "جنوب سيناء", "en": "South Sinai", "id": "south_sinai"},
]

def identify_governorate(filename_or_url):
    decoded = urllib.parse.unquote(filename_or_url).lower()
    if "summary" in decoded or "ملخص" in decoded or "oecd" in decoded:
        return {"ar": "تقرير الملخص العام", "en": "Summary Report", "id": "summary_report", "is_summary": True}
    
    for g in GOVERNORATES:
        norm_ar = g["ar"].replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي").replace(" ", "")
        norm_decoded = decoded.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي").replace("_", "").replace(" ", "").replace("-", "")
        
        # Check Arabic
        if norm_ar in norm_decoded:
            return {**g, "is_summary": False}
        
        # Check English
        norm_en = g["en"].lower().replace(" ", "").replace("-", "")
        if norm_en in norm_decoded:
            return {**g, "is_summary": False}
        if g["id"].replace("_", "") in norm_decoded:
            return {**g, "is_summary": False}
            
    # Special fallbacks
    if "alex" in decoded or "اسكندرية" in decoded:
        return {"ar": "الإسكندرية", "en": "Alexandria", "id": "alexandria", "is_summary": False}
    if "cairo" in decoded or "القاهرة" in decoded:
        return {"ar": "القاهرة", "en": "Cairo", "id": "cairo", "is_summary": False}
    if "behira" in decoded or "البحيرة" in decoded:
        return {"ar": "البحيرة", "en": "Beheira", "id": "beheira", "is_summary": False}
    if "portsaid" in decoded or "بورسعيد" in decoded:
        return {"ar": "بورسعيد", "en": "Port Said", "id": "portsaid", "is_summary": False}
    if "redsea" in decoded or "البحر" in decoded:
        return {"ar": "البحر الأحمر", "en": "Red Sea", "id": "red_sea", "is_summary": False}
    if "newvalley" in decoded or "الوادي" in decoded:
        return {"ar": "الوادي الجديد", "en": "New Valley", "id": "new_valley", "is_summary": False}
        
    return {"ar": "غير محدد", "en": "Unknown", "id": "unknown", "is_summary": False}

def download_file(item):
    url = item["url"]
    dest_dir = item["dest_dir"]
    edition = item["edition"]
    
    os.makedirs(dest_dir, exist_ok=True)
    raw_fname = os.path.basename(urllib.parse.urlparse(url).path)
    decoded_fname = urllib.parse.unquote(raw_fname)
    
    # Clean filename for Windows filesystem
    safe_fname = re.sub(r'[\\/*?:"<>|┬⌐]', '_', decoded_fname)
    dest_path = os.path.join(dest_dir, safe_fname)
    
    gov_info = identify_governorate(decoded_fname)
    
    result = {
        "edition": edition,
        "url": url,
        "filename": safe_fname,
        "path": os.path.abspath(dest_path),
        "governorate_ar": gov_info["ar"],
        "governorate_en": gov_info["en"],
        "governorate_id": gov_info["id"],
        "is_summary": gov_info["is_summary"],
        "status": "pending",
        "file_size": 0,
        "error": None
    }
    
    # If already downloaded and > 10KB, skip
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
        result["status"] = "already_downloaded"
        result["file_size"] = os.path.getsize(dest_path)
        print(f"[SKIP] {safe_fname} ({result['file_size']} bytes)")
        return result

    for attempt in range(1, 4):
        try:
            print(f"[DOWNLOADING] ({attempt}/3) {url} -> {safe_fname}")
            resp = requests.get(url, headers=HEADERS, verify=False, timeout=60, stream=True)
            if resp.status_code == 200:
                with open(dest_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                size = os.path.getsize(dest_path)
                result["status"] = "success"
                result["file_size"] = size
                print(f"[SUCCESS] {safe_fname} ({size} bytes)")
                return result
            else:
                result["error"] = f"HTTP {resp.status_code}"
        except Exception as e:
            result["error"] = str(e)
            time.sleep(2)
            
    result["status"] = "failed"
    print(f"[FAILED] {safe_fname}: {result['error']}")
    return result

def main():
    with open("data/raw_html/page_inspection.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    tasks = []
    
    # Edition 1
    for url in data["edition_1"]["all_pdfs"]:
        tasks.append({
            "url": url,
            "dest_dir": E1_DIR,
            "edition": 1
        })
        
    # Edition 2
    for url in data["edition_2"]["all_pdfs"]:
        tasks.append({
            "url": url,
            "dest_dir": E2_DIR,
            "edition": 2
        })
        
    print(f"Total reports to download: {len(tasks)}")
    
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_task = {executor.submit(download_file, t): t for t in tasks}
        for future in as_completed(future_to_task):
            res = future.result()
            results.append(res)
            
    # Save manifest
    os.makedirs("data", exist_ok=True)
    with open("data/download_manifest.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    success_count = sum(1 for r in results if r["status"] in ("success", "already_downloaded"))
    failed_count = sum(1 for r in results if r["status"] == "failed")
    print(f"\nDownload finished! Success: {success_count}/{len(tasks)}, Failed: {failed_count}")

if __name__ == "__main__":
    main()
