import os
import re
import requests
import json
import urllib.parse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PAGES = {
    "edition_1": "https://mped.gov.eg/DynamicPage?id=107",
    "edition_2": "https://mped.gov.eg/DynamicPage?id=118"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8"
}

def inspect_page(edition_key, url):
    print(f"Fetching {edition_key}: {url}...")
    try:
        resp = requests.get(url, headers=HEADERS, verify=False, timeout=30)
        print(f"Status: {resp.status_code}, Length: {len(resp.text)}")
        html = resp.text
        
        # Save raw HTML for inspection
        os.makedirs("data/raw_html", exist_ok=True)
        with open(f"data/raw_html/{edition_key}.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        # Search for PDF links and anchor tags
        pdf_pattern = re.compile(r'href=["\']([^"\']+\.pdf[^"\']*)["\']', re.IGNORECASE)
        pdfs = pdf_pattern.findall(html)
        print(f"Found {len(pdfs)} raw PDF links with regex")
        
        # Search for any dynamic links, download links, or governorate links
        # Find <a> tags
        a_tags = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE)
        print(f"Found {len(a_tags)} <a> tags")
        
        reports = []
        for href, text in a_tags:
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            if '.pdf' in href.lower() or 'download' in href.lower() or 'report' in href.lower() or 'file' in href.lower() or 'upload' in href.lower() or 'drive' in href.lower() or 'media' in href.lower():
                full_url = urllib.parse.urljoin(url, href)
                reports.append({"href": full_url, "text": clean_text})
        
        print(f"Matched {len(reports)} relevant links for {edition_key}")
        for r in reports[:10]:
            print(f"  - [{r['text'][:50]}] -> {r['href']}")
            
        return {
            "url": url,
            "status": resp.status_code,
            "reports": reports,
            "all_pdfs": [urllib.parse.urljoin(url, p) for p in pdfs]
        }
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    results = {}
    for k, u in PAGES.items():
        results[k] = inspect_page(k, u)
        
    with open("data/raw_html/page_inspection.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Inspection complete.")
