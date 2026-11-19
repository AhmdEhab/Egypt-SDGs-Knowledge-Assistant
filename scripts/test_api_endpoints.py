import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import time
import requests
import uvicorn
from backend.main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8899, log_level="warning")

if __name__ == "__main__":
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(2)
    
    base_url = "http://127.0.0.1:8899"
    
    print("\n--- Testing GET /api/status ---")
    r = requests.get(f"{base_url}/api/status")
    print("Status:", r.status_code, r.json())
    assert r.status_code == 200
    
    print("\n--- Testing GET /api/governorates ---")
    r = requests.get(f"{base_url}/api/governorates")
    print("Gov count:", len(r.json()))
    assert len(r.json()) == 27
    
    print("\n--- Testing GET /api/sdgs ---")
    r = requests.get(f"{base_url}/api/sdgs")
    print("SDGs count:", len(r.json()))
    assert len(r.json()) == 13
    
    print("\n--- Testing POST /api/chat (Comparison) ---")
    r = requests.post(f"{base_url}/api/chat", json={
        "message": "قارن أداء محافظة القاهرة ومحافظة الإسكندرية.",
        "history": [],
        "language": "ar"
    })
    print("Status:", r.status_code)
    res = r.json()
    print("Answer length:", len(res["answer"]))
    print("Citations count:", len(res["citations"]))
    print("Has Table:", bool(res["table"]))
    print("Has Chart:", bool(res["chart"]))
    print("Followups:", res["followups"])
    assert r.status_code == 200
    assert bool(res["table"]) is True
    
    print("\n--- Testing POST /api/chat (Specific SDG) ---")
    r = requests.post(f"{base_url}/api/chat", json={
        "message": "ما هو أداء المحافظات في الهدف الرابع الخاص بالتعليم؟",
        "history": [],
        "language": "ar"
    })
    res = r.json()
    print("Answer preview:", res["answer"][:150])
    print("Has Chart:", bool(res["chart"]))
    assert r.status_code == 200
    
    print("\n--- Testing POST /api/chat (English Query) ---")
    r = requests.post(f"{base_url}/api/chat", json={
        "message": "What are the main sustainable development challenges in Gharbia?",
        "history": [],
        "language": "en"
    })
    res = r.json()
    print("Answer preview:", res["answer"][:150])
    assert r.status_code == 200
    
    print("\n--- Testing POST /api/chat (Out of Domain Query) ---")
    r = requests.post(f"{base_url}/api/chat", json={
        "message": "كيف تصنع البيتزا الإيطالية؟",
        "history": [],
        "language": "ar"
    })
    res = r.json()
    print("Answer:", res["answer"])
    assert "لا تتوفر معلومات كافية عن هذا السؤال في التقارير الرسمية" in res["answer"]
    
    print("\n--- Testing GET / (Frontend serving) ---")
    r = requests.get(f"{base_url}/")
    print("HTML Length:", len(r.text))
    assert r.status_code == 200
    assert "Egypt SDGs Knowledge Assistant" in r.text
    
    print("\nALL API ENDPOINTS TESTED AND VERIFIED SUCCESSFULLY!")
