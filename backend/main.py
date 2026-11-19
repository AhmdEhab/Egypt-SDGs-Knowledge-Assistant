import os
import sys
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from backend.rag_engine import RAGEngine

app = FastAPI(
    title="Egypt SDGs Knowledge Assistant",
    description="AI-Powered Knowledge Chatbot for Egypt's Sustainable Development Localization Reports (Ministry of Planning and Economic Development)",
    version="1.0.0"
)

# Enable CORS for presentations and multi-device access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = RAGEngine()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []
    language: Optional[str] = "ar"

@app.get("/api/status")
@app.get("/status")
def get_status():
    return {
        "status": "online",
        "app_name": "Egypt SDGs Knowledge Assistant",
        "total_reports": 55,
        "total_pages": 1053,
        "total_chunks": 1037,
        "llm_provider": "Gemini API" if os.environ.get("GEMINI_API_KEY") else "Built-in High Precision Engine",
        "has_gemini_key": bool(os.environ.get("GEMINI_API_KEY")),
        "presentation_mode": True
    }

@app.get("/api/governorates")
@app.get("/governorates")
def get_governorates():
    govs = engine.metrics_db.get("governorates", {})
    return list(govs.values())

@app.get("/api/sdgs")
@app.get("/sdgs")
def get_sdgs():
    return engine.metrics_db.get("sdg_definitions", [])

@app.get("/api/compare")
@app.get("/compare")
def compare_governorates(gov1: str, gov2: str, lang: str = "ar"):
    table, chart = engine._build_gov_comparison_data(gov1, gov2, lang)
    return {
        "table": table,
        "chart": chart
    }

@app.get("/api/ingestion/summary")
@app.get("/ingestion/summary")
def get_ingestion_summary():
    report_path = os.path.join(os.path.dirname(__file__), "..", "data", "ingestion_report.json")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"error": "Report not found"}

@app.post("/api/chat")
@app.post("/chat")
def chat(request: ChatRequest):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    try:
        response = engine.generate_response(request.message, request.history)
        
        # Suggest intuitive follow-ups based on query entities
        followups = []
        entities = response.get("entities", {})
        lang = entities.get("lang", request.language or "ar")
        
        if entities.get("governorates"):
            gov_id = entities["governorates"][0]
            g_meta = engine.metrics_db.get("governorates", {}).get(gov_id, {})
            name = g_meta.get("ar" if lang == "ar" else "en", gov_id)
            if lang == "ar":
                followups.append(f"ما هي مستهدفات 2030 لمحافظة {name}؟")
                followups.append(f"ما هي أهم المؤشرات التي تحتاج إلى تحسين في {name}؟")
                followups.append(f"هل حصل تحسن في {name} بين الإصدار الأول والثاني؟")
            else:
                followups.append(f"What are the 2030 targets for {name}?")
                followups.append(f"What are the priority indicators needing improvement in {name}?")
        elif entities.get("sdgs"):
            num = entities["sdgs"][0]
            if lang == "ar":
                followups.append(f"إيه المحافظات اللي أداؤها أفضل في الهدف {num}؟")
                followups.append(f"قارن أداء القاهرة والإسكندرية في الهدف {num}.")
            else:
                followups.append(f"Which governorates rank highest in SDG {num}?")
        else:
            if lang == "ar":
                followups.append("ما هو وضع محافظة الغربية في تحقيق أهداف التنمية المستدامة؟")
                followups.append("قارن أداء محافظة القاهرة ومحافظة الإسكندرية.")
                followups.append("ما هو أداء المحافظات في الهدف الرابع الخاص بالتعليم؟")
            else:
                followups.append("What are the main sustainable development challenges in Gharbia?")
                followups.append("Compare the performance of Cairo and Alexandria.")
                
        return {
            "answer": response["answer"],
            "citations": response["citations"],
            "table": response["table"],
            "chart": response["chart"],
            "entities": response["entities"],
            "followups": followups[:3]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Find static/public directory
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
public_dir = os.path.join(root_dir, "public")
frontend_dir = os.path.join(root_dir, "frontend")

static_dir_to_use = public_dir if os.path.exists(public_dir) else frontend_dir
if os.path.exists(static_dir_to_use):
    app.mount("/static", StaticFiles(directory=static_dir_to_use), name="static")

@app.get("/")
@app.get("/api")
@app.get("/api/")
@app.get("/api/index")
@app.get("/api/index.py")
def serve_index():
    for candidate in [
        os.path.join(public_dir, "index.html"),
        os.path.join(frontend_dir, "index.html")
    ]:
        if os.path.exists(candidate):
            return FileResponse(candidate)
    return {"message": "Egypt SDGs Knowledge Assistant API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
