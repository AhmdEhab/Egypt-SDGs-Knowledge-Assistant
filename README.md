# Egypt SDGs Knowledge Assistant | مساعد المعرفة لأهداف التنمية المستدامة في مصر

An AI-powered Knowledge Chatbot built for live presentations, executive demonstrations, and policy research on Egypt's official Sustainable Development Goals (SDGs) Localization Reports published by the **Ministry of Planning and Economic Development (MPED)**.

---

## 🏛️ Official Knowledge Sources

The knowledge base is built from the two official MPED sources:

1. **Source 1 – First Edition (2021/2022)**:
   - [https://mped.gov.eg/DynamicPage?id=107](https://mped.gov.eg/DynamicPage?id=107)
   - Partners: Ministry of Planning and Economic Development & United Nations Population Fund (UNFPA).
   - Reports: **27 Governorate Reports**.
   - Indicators: **32 localized indicators** covering demographic profiles, distance to 2030 targets, national averages, and priority recommendations.

2. **Source 2 – Second Edition (2024/2025)**:
   - [https://mped.gov.eg/DynamicPage?id=118](https://mped.gov.eg/DynamicPage?id=118)
   - Partners: Ministry of Planning and Economic Development and International Cooperation, United Nations Development Programme (UNDP), and Baseera.
   - Reports: **27 Governorate Reports** + **1 Summary Report**.
   - Indicators: Expanded to **50 indicators** with OECD composite index scoring (0–100 scale) per SDG across all governorates.

---

## 📊 Ingestion & Knowledge Base Verification

| Metric | Value |
|---|---|
| **Total Official PDF Reports Processed** | **55 of 55 (100% Success)** |
| **First Edition Reports** | 27 Governorate Reports |
| **Second Edition Reports** | 27 Governorate Reports + 1 Summary Report (28 total) |
| **Total Pages Indexed** | **1,053 Pages** |
| **Searchable Document Chunks** | **1,037 Chunks** |
| **Extraction Errors / Skipped Files** | **0** |
| **Knowledge Base Size** | ~3.2 MB (In-memory optimized BM25 + Vector + Structured Metrics) |

For the full breakdown of all 55 reports, see [`ingestion_report.md`](C:\Users\aehab\.gemini\antigravity\brain\98f920a2-b559-42a2-a7c3-2a8802984083\ingestion_report.md) or `data/ingestion_report.json`.

---

## 🧠 Chatbot Intelligence & Retrieval Architecture

- **Retrieval Engine**:
  - Inverted BM25 index with Arabic normalization (harakat, tatweel, letter unification) and stemming.
  - Strict metadata filtering by governorate (27 Egyptian governorates), edition (1 vs 2 vs both), and SDG (1 to 17).
  - Out-of-Domain Relevance Gate: If a query is outside the domain, the chatbot strictly responds with:
    > *"لا تتوفر معلومات كافية عن هذا السؤال في التقارير الرسمية المتاحة ضمن قاعدة بيانات المساعد."*
- **Structured Indicator Database**:
  - Exact OECD 0–100 scores for every governorate across all SDGs.
  - Generates side-by-side comparison tables and dynamic Chart.js bar charts automatically.
- **Dual-Mode Response Generation**:
  - **With `GEMINI_API_KEY`**: Integrates with Google Gemini (`gemini-2.5-flash`) with prompt boundaries strictly preventing hallucinations and mandating page-level citations.
  - **Built-in Presentation Fallback Engine**: If no API key is set, the assistant runs 100% locally with high precision, extracting verified figures, comparisons, and source citations directly.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14.0)

### 2. Environment Configuration (Optional)
If you wish to enable the Gemini API for natural generative synthesis:
```bash
# Windows PowerShell
$env:GEMINI_API_KEY="your-gemini-api-key-here"

# Or Windows Command Prompt
set GEMINI_API_KEY=your-gemini-api-key-here
```
*(If no API key is provided, the chatbot runs reliably using the built-in verified engine).*

### 3. Run the Application
```bash
python run.py
```
Or double-click `start.bat`.

Open your browser at:
```
http://localhost:8000
```

---

## 🎯 Presentation Demonstration Scenarios

Use the interactive suggestion chips or type live questions:

1. **Explore a Governorate**:
   - `ما هو وضع محافظة الغربية في تحقيق أهداف التنمية المستدامة؟`
   - `What are the main sustainable development challenges in Gharbia?`
2. **Compare Two Governorates**:
   - `قارن أداء محافظة القاهرة ومحافظة الإسكندرية.`
   - `Compare the performance of Cairo and Alexandria.`
   *(Generates structured comparison table and interactive bar chart)*
3. **Explore an SDG**:
   - `ما هو أداء المحافظات في الهدف الرابع الخاص بالتعليم؟`
   *(Ranks Port Said (88/100), Cairo (85/100), Alexandria (83/100) with interactive chart)*
4. **Analyze Indicators & Challenges**:
   - `ما هي أهم المؤشرات التي تحتاج إلى تحسين في محافظة البحيرة؟`
5. **Compare Report Editions**:
   - `هل حصل تحسن بين الإصدار الأول والإصدار الثاني في الغربية؟`
   *(Explains the expansion from 32 to 50 indicators and OECD methodology)*
6. **Strict Out-of-Domain Rejection**:
   - `ما هي تفاصيل برنامج رحلات الفضاء إلى كوكب المريخ؟`
   *(Returns: "لا تتوفر معلومات كافية عن هذا السؤال في التقارير الرسمية المتاحة ضمن قاعدة بيانات المساعد.")*

---

## 📁 Project Structure

```
chatbot/
├── backend/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application & REST endpoints
│   └── rag_engine.py               # RAG retrieval, BM25, and response synthesis
├── data/
│   ├── processed/
│   │   ├── chunks.json             # 1,037 indexed chunks with page metadata
│   │   ├── governorate_metrics.json# Structured OECD scores and indicator tables
│   │   └── knowledge_base.json     # Serialized BM25 search index
│   ├── reports/
│   │   ├── edition_1/              # 27 First Edition PDF reports
│   │   └── edition_2/              # 27 Second Edition PDF reports + Summary Report
│   ├── download_manifest.json      # File download verification manifest
│   └── ingestion_report.json       # Detailed ingestion stats
├── frontend/
│   ├── index.html                  # Responsive presentation UI
│   ├── style.css                   # Modern styling & theme
│   └── app.js                      # Chat interaction, tables & Chart.js rendering
├── scripts/
│   ├── download_reports.py         # Batch parallel downloader for 55 reports
│   ├── extract_and_index.py        # PDF text & table extractor
│   ├── build_knowledge_base.py     # Search index and metrics builder
│   ├── test_rag_pipeline.py        # Automated test suite for core inquiries
│   └── test_api_endpoints.py       # End-to-end API and UI test suite
├── run.py                          # Application startup script
├── start.bat                       # Windows one-click batch launcher
└── README.md                       # Comprehensive system documentation
```
