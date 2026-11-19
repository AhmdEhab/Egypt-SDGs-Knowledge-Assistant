import os
import re
import json
import math
from collections import defaultdict, Counter

# Path configs
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
CHUNKS_FILE = os.path.join(DATA_DIR, "chunks.json")
METRICS_FILE = os.path.join(DATA_DIR, "governorate_metrics.json")
KB_FILE = os.path.join(DATA_DIR, "knowledge_base.json")

UNAVAILABLE_MSG_AR = "لا تتوفر معلومات كافية عن هذا السؤال في التقارير الرسمية المتاحة ضمن قاعدة بيانات المساعد."
UNAVAILABLE_MSG_EN = "Sufficient information is not available for this question in the official reports within the assistant's knowledge base."

# Core SDG Definitions & Keywords
SDG_INFO = {
    1: {"ar": "القضاء على الفقر", "en": "No Poverty", "keywords": ["فقر", "poverty", "خط الفقر", "المعونة", "الدخل"]},
    2: {"ar": "القضاء التام على الجوع", "en": "Zero Hunger", "keywords": ["جوع", "hunger", "سوء التغذية", "تقزم", "هزال", "أنيميا", "stunting", "wasting"]},
    3: {"ar": "الصحة الجيدة والرفاه", "en": "Good Health and Well-being", "keywords": ["صحة", "health", "وفيات", "إنجاب", "أطباء", "تنظيم الأسرة", "ولادة", "مستشفى", "mortality", "fertility"]},
    4: {"ar": "التعليم الجيد", "en": "Quality Education", "keywords": ["تعليم", "education", "أمية", "مدارس", "إعاقة", "قيد", "ابتدائي", "illiteracy", "schools"]},
    5: {"ar": "المساواة بين الجنسين", "en": "Gender Equality", "keywords": ["مساواة", "gender", "إناث", "مرأة", "نساء", "برلمان", "ختان", "عنف"]},
    6: {"ar": "المياه النظيفة والنظافة الصحية", "en": "Clean Water and Sanitation", "keywords": ["مياه", "water", "صرف", "نظافة", "شرب", "sanitation", "toilet"]},
    7: {"ar": "طاقة نظيفة وبأسعار معقولة", "en": "Affordable and Clean Energy", "keywords": ["طاقة", "كهرباء", "energy", "electricity", "غاز"]},
    8: {"ar": "العمل اللائق ونمو الاقتصاد", "en": "Decent Work and Economic Growth", "keywords": ["عمل", "بطالة", "نمو", "اقتصاد", "تدريب", "قوة العمل", "unemployment", "gdp"]},
    9: {"ar": "الصناعة والابتكار والهياكل الأساسية", "en": "Industry, Innovation and Infrastructure", "keywords": ["صناعة", "ابتكار", "بنية تحتية", "industry", "innovation"]},
    10: {"ar": "الحد من أوجه عدم المساواة", "en": "Reduced Inequalities", "keywords": ["عدم مساواة", "فروق", "inequality"]},
    11: {"ar": "مدن ومجتمعات محلية مستدامة", "en": "Sustainable Cities and Communities", "keywords": ["مدن", "عشوائيات", "عشوائية", "سكن", "urban", "cities", "slums"]},
    12: {"ar": "الاستهلاك والإنتاج المسؤولان", "en": "Responsible Consumption and Production", "keywords": ["استهلاك", "إنتاج", "consumption"]},
    13: {"ar": "العمل المناخي", "en": "Climate Action", "keywords": ["مناخ", "بيئة", "climate"]},
    14: {"ar": "الحياة تحت الماء", "en": "Life Below Water", "keywords": ["حياة تحت الماء", "بحار", "marine"]},
    15: {"ar": "الحياة في البر", "en": "Life on Land", "keywords": ["حياة في البر", "تصحر", "terrestrial"]},
    16: {"ar": "السلام والعدل والمؤسسات القوية", "en": "Peace, Justice and Strong Institutions", "keywords": ["سلام", "عدل", "عقاب", "أطفال", "justice", "institutions"]},
    17: {"ar": "عقد الشراكات لتحقيق الأهداف", "en": "Partnerships for the Goals", "keywords": ["شراكات", "إنترنت", "حاسب", "اتصالات", "partnerships", "internet"]}
}

GOVERNORATE_ALIASES = {
    "cairo": ["القاهرة", "قاهرة", "cairo"],
    "alexandria": ["الإسكندرية", "الاسكندرية", "اسكندرية", "alexandria", "alex"],
    "portsaid": ["بورسعيد", "بور سعيد", "port said", "portsaid"],
    "suez": ["السويس", "سويس", "suez"],
    "damietta": ["دمياط", "damietta"],
    "dakahlia": ["الدقهلية", "دقهلية", "dakahlia"],
    "sharkia": ["الشرقية", "شرقية", "sharkia"],
    "qalyubia": ["القليوبية", "قليوبية", "qalyubia"],
    "kafr_elsheikh": ["كفر الشيخ", "كفرالشيخ", "kafr el-sheikh", "kafr el sheikh", "kafr elsheikh"],
    "gharbia": ["الغربية", "غربية", "gharbia"],
    "menofia": ["المنوفية", "منوفية", "menofia", "monufia"],
    "beheira": ["البحيرة", "بحيرة", "beheira", "behira"],
    "ismailia": ["الإسماعيلية", "الاسماعيلية", "اسماعيلية", "ismailia"],
    "giza": ["الجيزة", "جيزة", "giza"],
    "beni_suef": ["بني سويف", "بنى سويف", "beni suef", "benisuef"],
    "faiyum": ["الفيوم", "فيوم", "faiyum", "fayoum"],
    "minya": ["المنيا", "منيا", "minya"],
    "assiut": ["أسيوط", "اسيوط", "assiut", "asyut"],
    "sohag": ["سوهاج", "sohag"],
    "qena": ["قنا", "qena"],
    "luxor": ["الأقصر", "الاقصر", "أقصر", "اقصر", "luxor"],
    "aswan": ["أسوان", "اسوان", "aswan"],
    "red_sea": ["البحر الأحمر", "البحر الاحمر", "بحر احمر", "red sea", "redsea"],
    "new_valley": ["الوادي الجديد", "الوادى الجديد", "وادي جديد", "new valley", "newvalley"],
    "matrouh": ["مطروح", "مرسى مطروح", "matrouh"],
    "north_sinai": ["شمال سيناء", "شمال سينا", "north sinai"],
    "south_sinai": ["جنوب سيناء", "جنوب سينا", "south sinai"]
}

# Domain vocabulary to verify relevance
DOMAIN_KEYWORDS = set("""
تنمية مستدامة توطين اهداف هدف مؤشر مؤشرات تقرير تقارير محافظة محافظات مستهدف مستهدفات 2030 رؤية مصر احصاء جهاز
فقر جوع صحة تعليم امية مساواة جنسين مياه صرف كهرباء بطالة عمل نمو صناعة عشوائيات اطفال وفيات انجاب تنظيم اسرة
تحسين تحديات معوقات اصدار اول ثاني
sdg sdgs indicator indicators egypt governorate localization report ranking oecd target targets score
""".split())

AR_STOPWORDS = set("""
و في من على الى إلى أن إن عن مع كان كانت هذا هذه تم ذلك التي الذي الذين أو ثم حتى إلا لم لن كل بعد قبل حيث بها به فيها فيه منه منها لها له وما وهو وهي تكون يكون كما منذ عند لدى بين ليس قد إيه ايه ماهو ما هو ماهي ما هي ماهم ماذا كيف هل
""".split())

EN_STOPWORDS = set("""
a an the is are was were in on at to for with by about of and or as that this it its they their from be been what which how does do did
""".split())

def normalize_text(text):
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ـ+', '', text)
    return text.lower()

def stem_word(w):
    # Remove common Arabic prefixes
    if len(w) > 4 and w.startswith("ال"):
        w = w[2:]
    if len(w) > 4 and w.startswith("وال"):
        w = w[3:]
    if len(w) > 4 and w.startswith("فال"):
        w = w[3:]
    if len(w) > 4 and w.startswith("بال"):
        w = w[3:]
    if len(w) > 4 and w.startswith("لل"):
        w = w[2:]
    return w

def tokenize(text):
    norm = normalize_text(text)
    words = re.findall(r'[\u0600-\u06FFa-zA-Z0-9]+', norm)
    return [w for w in words if len(w) > 1 and w not in AR_STOPWORDS and w not in EN_STOPWORDS]

class RAGEngine:
    def __init__(self):
        print("Initializing enhanced RAGEngine...")
        with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)
        with open(METRICS_FILE, "r", encoding="utf-8") as f:
            self.metrics_db = json.load(f)
        with open(KB_FILE, "r", encoding="utf-8") as f:
            self.kb_index = json.load(f)
            
        self.doc_count = self.kb_index["doc_count"]
        self.avg_doc_len = self.kb_index["avg_doc_len"]
        self.doc_len = self.kb_index["doc_len"]
        self.idf = self.kb_index["idf"]
        self.inverted_index = self.kb_index["inverted_index"]
        print(f"Enhanced RAGEngine ready with {len(self.chunks)} chunks.")

    def detect_intent_and_entities(self, query):
        query_norm = normalize_text(query)
        
        # 1. Detect governorates using broad Unicode word boundary
        detected_govs = []
        for gid, aliases in GOVERNORATE_ALIASES.items():
            for alias in aliases:
                norm_alias = normalize_text(alias)
                pattern = rf"(?:^|[^\w])(?:و|ف|ب|ل|ك)?(?:محافظ[ةه]\s*)?{re.escape(norm_alias)}(?:$|[^\w])"
                if re.search(pattern, query_norm):
                    if gid not in detected_govs:
                        detected_govs.append(gid)
                    break

        if len(detected_govs) > 1:
            def first_pos(gid):
                for a in GOVERNORATE_ALIASES[gid]:
                    pos = query_norm.find(normalize_text(a))
                    if pos != -1:
                        return pos
                return 9999
            detected_govs.sort(key=first_pos)

        # 2. Detect SDGs
        detected_sdgs = []
        num_names = {
            1: ["الاول", "1", "one"], 2: ["الثاني", "2", "two"], 3: ["الثالث", "3", "three"],
            4: ["الرابع", "4", "four"], 5: ["الخامس", "5", "five"], 6: ["السادس", "6", "six"],
            7: ["السابع", "7", "seven"], 8: ["الثامن", "8", "eight"], 9: ["التاسع", "9", "nine"],
            10: ["العاشر", "10", "ten"], 11: ["الحادي عشر", "11"], 12: ["الثاني عشر", "12"],
            13: ["الثالث عشر", "13"], 14: ["الرابع عشر", "14"], 15: ["الخامس عشر", "15"],
            16: ["السادس عشر", "16"], 17: ["السابع عشر", "17"]
        }
        for sdg_num, info in SDG_INFO.items():
            matched = False
            for num_rep in num_names.get(sdg_num, []):
                pats = [
                    rf"(?:الهدف|هدف|sdg)\s*(?:رقم\s*)?{re.escape(num_rep)}(?:$|[^\w])",
                    rf"\b{re.escape(num_rep)}\s*(?:الاممي|الأممي)\b"
                ]
                for p in pats:
                    if re.search(p, query_norm):
                        detected_sdgs.append(sdg_num)
                        matched = True
                        break
                if matched:
                    break
            if not matched:
                for kw in info["keywords"]:
                    norm_kw = normalize_text(kw)
                    if re.search(rf"(?:^|[^\w]){re.escape(norm_kw)}(?:$|[^\w])", query_norm):
                        detected_sdgs.append(sdg_num)
                        break

        # 3. Detect Edition preferences
        edition_target = None
        is_edition_comparison = any(w in query_norm for w in [
            "بين الاصدار", "مقارنة بين الاصدارين", "الاصدار الاول والثاني", "تحسن بين الاصدار",
            "بين الاصدارين", "فرق بين الاصدارين", "compare editions", "first and second", "الاول والثاني"
        ])
        if is_edition_comparison:
            edition_target = "both"
        elif any(w in query_norm for w in ["الاصدار الاول", "الاولى", "الطبعة الاولى", "edition 1", "first edition", "2021"]):
            edition_target = 1
        elif any(w in query_norm for w in ["الاصدار الثاني", "الثانية", "الطبعة الثانية", "edition 2", "second edition", "2024", "2023"]):
            edition_target = 2

        # 4. Intent detection
        is_comparison = len(detected_govs) >= 2 or any(w in query_norm for w in ["قارن", "مقارنة", "compare", "فرق بين"])
        is_ranking = any(w in query_norm for w in ["افضل", "احسن", "اعلى", "اقل", "ترتيب", "best", "highest", "lowest", "ranking", "اقوى"])
        is_targets = any(w in query_norm for w in ["مستهدفات", "مستهدف", "2030", "targets", "target", "رؤية"])
        is_challenges = any(w in query_norm for w in ["تحديات", "تحسين", "معوقات", "challenges", "improve", "needs", "نقص"])
        
        # Check language
        has_arabic = bool(re.search(r'[\u0600-\u06FF]', query))
        lang = "ar" if has_arabic else "en"

        # Check domain relevance strictly
        tokens = tokenize(query)
        stemmed_tokens = [stem_word(t) for t in tokens]
        domain_matches = sum(1 for t in stemmed_tokens if t in DOMAIN_KEYWORDS or any(dk in t for dk in ["تنمي", "مؤشر", "هدف", "محافظ", "تقرير", "مستهدف", "فقر", "تعليم", "صحة", "بطال", "sdg"]))
        is_domain_relevant = bool(
            detected_govs or 
            detected_sdgs or 
            domain_matches > 0 or 
            is_comparison or 
            is_targets or 
            is_challenges or 
            is_edition_comparison
        )

        return {
            "query": query,
            "lang": lang,
            "governorates": detected_govs,
            "sdgs": sorted(list(set(detected_sdgs))),
            "edition": edition_target,
            "is_comparison": is_comparison,
            "is_ranking": is_ranking,
            "is_targets": is_targets,
            "is_challenges": is_challenges,
            "is_edition_comparison": is_edition_comparison,
            "is_domain_relevant": is_domain_relevant
        }

    def search_chunks(self, query, entities, top_k=6):
        query_tokens = tokenize(query)
        scores = defaultdict(float)
        
        k1 = 1.5
        b = 0.75
        for token in query_tokens:
            stemmed = stem_word(token)
            # Search both raw token and stemmed token
            for search_term in set([token, stemmed]):
                if search_term not in self.idf:
                    continue
                idf_val = self.idf[search_term]
                postings = self.inverted_index.get(search_term, [])
                for doc_id, freq in postings:
                    dl = self.doc_len[doc_id]
                    denom = freq + k1 * (1.0 - b + b * (dl / self.avg_doc_len))
                    score = idf_val * (freq * (k1 + 1.0)) / denom
                    scores[doc_id] += score
                
        # Boost based on detected entities
        for doc_id in list(scores.keys()):
            chunk = self.chunks[doc_id]
            if entities["governorates"]:
                if chunk["governorate_id"] in entities["governorates"]:
                    scores[doc_id] *= 4.0
                else:
                    scores[doc_id] *= 0.2
                    
            if entities["sdgs"]:
                chunk_sdgs = chunk.get("sdg_numbers", [])
                if any(s in chunk_sdgs for s in entities["sdgs"]):
                    scores[doc_id] *= 2.5
                    
            if entities["edition"] in (1, 2):
                if chunk["edition"] == entities["edition"]:
                    scores[doc_id] *= 2.0
                else:
                    scores[doc_id] *= 0.5
            elif entities["edition"] == "both":
                scores[doc_id] *= 1.5

            if entities["is_ranking"] or not entities["governorates"]:
                if chunk["is_summary"]:
                    scores[doc_id] *= 2.5

        # If governorate detected but no BM25 scores yet (e.g. short query), add governorate chunks directly
        if entities["governorates"] and len(scores) < top_k:
            for gid in entities["governorates"]:
                matching = [i for i, c in enumerate(self.chunks) if c["governorate_id"] == gid]
                for doc_id in matching[:6]:
                    scores[doc_id] += 5.0

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_chunks = [self.chunks[doc_id] for doc_id, _ in ranked[:top_k]]
        return top_chunks

    def generate_response(self, query, history=None):
        entities = self.detect_intent_and_entities(query)
        lang = entities["lang"]
        
        # Follow-up context handling
        if history and not entities["governorates"] and not entities["sdgs"]:
            for prev in reversed(history):
                prev_text = prev.get("content", "")
                prev_entities = self.detect_intent_and_entities(prev_text)
                if prev_entities["governorates"] and not entities["governorates"]:
                    entities["governorates"] = prev_entities["governorates"]
                if prev_entities["sdgs"] and not entities["sdgs"]:
                    entities["sdgs"] = prev_entities["sdgs"]
                if entities["governorates"] or entities["sdgs"]:
                    entities["is_domain_relevant"] = True
                    break

        if not entities["is_domain_relevant"]:
            msg = UNAVAILABLE_MSG_AR if lang == "ar" else UNAVAILABLE_MSG_EN
            return {
                "answer": msg,
                "citations": [],
                "table": None,
                "chart": None,
                "entities": entities
            }

        retrieved_chunks = self.search_chunks(query, entities, top_k=6)
        
        if not retrieved_chunks:
            msg = UNAVAILABLE_MSG_AR if lang == "ar" else UNAVAILABLE_MSG_EN
            return {
                "answer": msg,
                "citations": [],
                "table": None,
                "chart": None,
                "entities": entities
            }

        citations = []
        seen_citations = set()
        for c in retrieved_chunks:
            cit_key = f"{c['filename']}_p{c['page_number']}"
            if cit_key not in seen_citations:
                seen_citations.add(cit_key)
                citations.append({
                    "report_name": c["filename"],
                    "governorate": c["governorate_ar"] if lang == "ar" else c["governorate_en"],
                    "edition": c["edition"],
                    "edition_name": c["edition_name"],
                    "page_number": c["page_number"],
                    "url": c["source_url"]
                })

        table_data = None
        chart_data = None
        
        if entities["is_comparison"] and len(entities["governorates"]) >= 2:
            gov1_id = entities["governorates"][0]
            gov2_id = entities["governorates"][1]
            table_data, chart_data = self._build_gov_comparison_data(gov1_id, gov2_id, lang)
            
        elif entities["sdgs"] and (entities["is_ranking"] or not entities["governorates"]):
            sdg_num = entities["sdgs"][0]
            table_data, chart_data = self._build_sdg_ranking_data(sdg_num, lang)

        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if gemini_api_key:
            try:
                answer = self._call_gemini_api(query, retrieved_chunks, entities, gemini_api_key, history)
                return {
                    "answer": answer,
                    "citations": citations,
                    "table": table_data,
                    "chart": chart_data,
                    "entities": entities
                }
            except Exception as e:
                print(f"Gemini API call failed, falling back to built-in generator: {e}")

        answer = self._synthesize_response(query, retrieved_chunks, entities, table_data, chart_data)
        
        return {
            "answer": answer,
            "citations": citations,
            "table": table_data,
            "chart": chart_data,
            "entities": entities
        }

    def _build_gov_comparison_data(self, gov1_id, gov2_id, lang):
        govs = self.metrics_db["governorates"]
        oecd = self.metrics_db["oecd_scores_by_sdg"]
        
        g1 = govs.get(gov1_id, {})
        g2 = govs.get(gov2_id, {})
        g1_name = g1.get("ar" if lang == "ar" else "en", gov1_id)
        g2_name = g2.get("ar" if lang == "ar" else "en", gov2_id)
        
        rows = []
        chart_labels = []
        g1_values = []
        g2_values = []
        
        for goal in self.metrics_db["sdg_definitions"]:
            num = goal["num"]
            goal_title = goal["name_ar"] if lang == "ar" else goal["name_en"]
            s1 = oecd.get(str(num), {}).get(gov1_id, oecd.get(num, {}).get(gov1_id, "N/A"))
            s2 = oecd.get(str(num), {}).get(gov2_id, oecd.get(num, {}).get(gov2_id, "N/A"))
            
            rows.append({
                "sdg_number": num,
                "sdg_name": f"{goal_title} (SDG {num})",
                "gov1_score": f"{s1}/100" if s1 != "N/A" else "غير متاح",
                "gov2_score": f"{s2}/100" if s2 != "N/A" else "غير متاح"
            })
            if isinstance(s1, (int, float)) and isinstance(s2, (int, float)):
                chart_labels.append(f"SDG {num}")
                g1_values.append(s1)
                g2_values.append(s2)
                
        table = {
            "title": f"مقارنة أداء {g1_name} و {g2_name} وفق مؤشرات أهداف التنمية المستدامة (منهجية OECD)" if lang == "ar" else f"Performance Comparison: {g1_name} vs {g2_name} (OECD SDG Scores)",
            "headers": ["الهدف الأممي" if lang == "ar" else "Goal", g1_name, g2_name],
            "rows": rows
        }
        
        chart = {
            "type": "bar",
            "title": f"مقارنة درجات الأداء الأممي (0-100)" if lang == "ar" else "SDG Performance Scores (0-100)",
            "labels": chart_labels,
            "datasets": [
                {"label": g1_name, "data": g1_values, "backgroundColor": "#10b981"},
                {"label": g2_name, "data": g2_values, "backgroundColor": "#3b82f6"}
            ]
        }
        return table, chart

    def _build_sdg_ranking_data(self, sdg_num, lang):
        oecd = self.metrics_db["oecd_scores_by_sdg"].get(str(sdg_num), self.metrics_db["oecd_scores_by_sdg"].get(sdg_num, {}))
        govs = self.metrics_db["governorates"]
        
        sorted_items = sorted(oecd.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else -1, reverse=True)
        goal_name = SDG_INFO.get(sdg_num, {}).get("ar" if lang == "ar" else "en", f"الهدف {sdg_num}")
        
        rows = []
        top_labels = []
        top_values = []
        
        for rank, (gid, score) in enumerate(sorted_items, 1):
            g_meta = govs.get(gid, {})
            name = g_meta.get("ar" if lang == "ar" else "en", gid)
            rows.append({
                "rank": rank,
                "governorate": name,
                "score": f"{score}/100" if isinstance(score, (int, float)) else "غير متاح"
            })
            if len(top_labels) < 10 and isinstance(score, (int, float)):
                top_labels.append(name)
                top_values.append(score)
                
        table = {
            "title": f"ترتيب المحافظات في {goal_name} (SDG {sdg_num}) - تقرير الملخص العام" if lang == "ar" else f"Governorate Rankings in SDG {sdg_num}: {goal_name}",
            "headers": ["الترتيب" if lang == "ar" else "Rank", "المحافظة" if lang == "ar" else "Governorate", "الدرجة (من 100)" if lang == "ar" else "Score (out of 100)"],
            "rows": rows[:15]
        }
        chart = {
            "type": "bar",
            "title": f"أعلى 10 محافظات أداءً في {goal_name}" if lang == "ar" else f"Top 10 Governorates in SDG {sdg_num}",
            "labels": top_labels,
            "datasets": [{
                "label": "الدرجة من 100" if lang == "ar" else "Score out of 100",
                "data": top_values,
                "backgroundColor": "#2563eb"
            }]
        }
        return table, chart

    def _synthesize_response(self, query, chunks, entities, table, chart):
        lang = entities["lang"]
        govs = entities["governorates"]
        sdgs = entities["sdgs"]

        def numeric_score(value):
            match = re.search(r"\d+(?:\.\d+)?", str(value))
            return float(match.group(0)) if match else None

        if entities["is_comparison"] and len(govs) >= 2 and table and table.get("rows"):
            g1_name = self.metrics_db["governorates"].get(govs[0], {}).get("ar" if lang == "ar" else "en", govs[0])
            g2_name = self.metrics_db["governorates"].get(govs[1], {}).get("ar" if lang == "ar" else "en", govs[1])
            differences = []
            for row in table["rows"]:
                s1 = numeric_score(row.get("gov1_score"))
                s2 = numeric_score(row.get("gov2_score"))
                if s1 is not None and s2 is not None:
                    goal_name = row.get("sdg_name", "")
                    if lang == "ar":
                        goal_name = re.sub(r"\s*\(SDG\s*(\d+)\)", r" (الهدف \1)", goal_name)
                    differences.append((goal_name, s1, s2, s1 - s2))
            if lang == "ar":
                parts = [f"### مقارنة {g1_name} و{g2_name}", "الدرجات تلخص أداء عدة مؤشرات لكل هدف، من 100؛ وليست نسبًا مئوية من السكان."]
                g1_leads = sorted((x for x in differences if x[3] > 0), key=lambda x: x[3], reverse=True)[:3]
                g2_leads = sorted((x for x in differences if x[3] < 0), key=lambda x: x[3])[:3]
                if g1_leads:
                    parts.append(f"\n**أهداف درجتها أعلى في {g1_name}:**")
                    parts.extend(f"- {name}: {s1:g} مقابل {s2:g} في {g2_name}." for name, s1, s2, _ in g1_leads)
                if g2_leads:
                    parts.append(f"\n**أهداف درجتها أعلى في {g2_name}:**")
                    parts.extend(f"- {name}: {s2:g} مقابل {s1:g} في {g1_name}." for name, s1, s2, _ in g2_leads)
                parts.append("\nالدرجة الأعلى تعني نتيجة أفضل في هذا المؤشر المركب فقط؛ ولا تكفي وحدها لتفسير كل المؤشرات داخل الهدف.")
            else:
                parts = [f"### {g1_name} vs. {g2_name}", "The table shows composite scores out of 100, not percentages of people."]
                for name, s1, s2, _ in sorted(differences, key=lambda x: abs(x[3]), reverse=True)[:5]:
                    leader = g1_name if s1 > s2 else g2_name if s2 > s1 else "Tie"
                    parts.append(f"- {name}: {s1:g}/100 vs. {s2:g}/100; higher score: {leader}.")
                parts.append("A higher composite score is not a substitute for reviewing the individual indicators.")
            return "\n".join(parts)

        if len(govs) == 1:
            gid = govs[0]
            g_meta = self.metrics_db["governorates"].get(gid, {})
            g_name = g_meta.get("ar" if lang == "ar" else "en", gid)

            if entities["is_targets"]:
                if lang == "ar":
                    return (
                        f"### مستهدفات 2030 في محافظة {g_name}\n"
                        "يحدد التقرير مستهدفًا لكل مؤشر، مع القيمة الحالية والفجوة عن المستهدف. هذه الأرقام تختلف من مؤشر لآخر.\n\n"
                        "المقاطع المستخرجة من الجداول لا تربط كل رقم بمؤشره بوضوح كافٍ، لذلك لن أذكر قيمة قد تكون في غير موضعها. "
                        "اذكر المؤشر الذي تريده، مثل الفقر أو التعليم، لأعرض بياناته ومصدره المحدد."
                    )
                return (
                    f"### 2030 targets for {g_name}\n"
                    "The report gives each indicator its own target, current value, and gap. The extracted table text does not reliably associate every number with its indicator, "
                    "so I will not guess. Ask about a specific indicator to narrow the source."
                )

            score_map = g_meta.get("sdg_scores_edition_2_summary", {})
            if not score_map:
                score_map = {
                    str(goal_num): self.metrics_db.get("oecd_scores_by_sdg", {}).get(str(goal_num), {}).get(gid)
                    for goal_num in range(1, 18)
                }
            goal_names = {
                str(item["num"]): item.get("name_ar" if lang == "ar" else "name_en", f"SDG {item['num']}")
                for item in self.metrics_db.get("sdg_definitions", [])
            }
            has_zero_score = any(numeric_score(value) == 0 for value in score_map.values())
            scores = []
            for number, value in score_map.items():
                score = numeric_score(value)
                if score is not None and score > 0:
                    name = goal_names.get(str(number), SDG_INFO.get(int(number), {}).get("ar" if lang == "ar" else "en", f"SDG {number}"))
                    scores.append((name, score))
            if lang == "ar":
                if entities["is_edition_comparison"]:
                    return (
                        f"### مقارنة الإصدارين لمحافظة {g_name}\n"
                        "الإصداران لا يعرضان دائمًا المؤشرات نفسها، كما تختلف طريقة التقييم بينهما. لذلك لا يعني اختلاف رقمين بالضرورة تحسنًا أو تراجعًا.\n\n"
                        "للمقارنة الدقيقة، يجب اختيار مؤشر واحد ومراجعة قيمته وسنته في كل إصدار. درجات الإصدار الثاني تلخص عدة مؤشرات لكل هدف، وليست نسبًا مئوية."
                    )
                if not scores:
                    return f"لا أجد في الملخص الحالي درجات منظمة كافية لعرضها لمحافظة {g_name}. جرّب سؤالًا عن مؤشر محدد."
                highest = sorted(scores, key=lambda item: item[1], reverse=True)[:3]
                lowest = sorted(scores, key=lambda item: item[1])[:3]
                parts = [
                    f"### ملخص أداء محافظة {g_name}",
                    "يعرض هذا الملخص درجات الإصدار الثاني (2024/2025). كل درجة تلخص عدة مؤشرات ضمن هدف واحد، من 100؛ وليست نسبة من السكان.",
                ]
                if entities["is_challenges"]:
                    parts.append("\n**أقل الدرجات المتاحة في الملخص:**")
                    parts.extend(f"- {name}: {score:g}/100." for name, score in lowest)
                    parts.append("\nهذه نقاط تستحق مراجعة المؤشرات التفصيلية؛ وليست بحد ذاتها توصيات رسمية أو تفسيرًا لأسباب النتيجة.")
                else:
                    parts.append("\n**أعلى الدرجات المتاحة:**")
                    parts.extend(f"- {name}: {score:g}/100." for name, score in highest)
                    parts.append("\n**أقل الدرجات المتاحة:**")
                    parts.extend(f"- {name}: {score:g}/100." for name, score in lowest)
                    parts.append("\nهذه الدرجات تعطي صورة عامة فقط؛ أما تفاصيل كل مؤشر فتجدها في المصادر المشار إليها أسفل الإجابة.")
                if has_zero_score:
                    parts.append("\nلم أدرج أي درجة صفرية؛ لأن الملخص لا يوضح هل تعني نتيجة فعلية أم أن البيانات غير متاحة.")
                return "\n".join(parts)

            if not scores:
                return f"The available structured summary does not contain reliable SDG scores for {g_name}. Ask about a specific indicator."
            highest = sorted(scores, key=lambda item: item[1], reverse=True)[:3]
            lowest = sorted(scores, key=lambda item: item[1])[:3]
            lines = [f"### {g_name}: SDG score summary", "Scores are out of 100 and are not population percentages.", "\n**Highest available scores:**"]
            lines.extend(f"- {name}: {score:g}/100." for name, score in highest)
            lines.append("\n**Lowest available scores:**")
            lines.extend(f"- {name}: {score:g}/100." for name, score in lowest)
            return "\n".join(lines)

        if sdgs and table and table.get("rows"):
            sdg_num = sdgs[0]
            sdg_meta = SDG_INFO.get(sdg_num, {"ar": f"الهدف {sdg_num}", "en": f"SDG {sdg_num}"})
            top_rows = table["rows"][:3]
            if lang == "ar":
                parts = [f"### أعلى المحافظات في {sdg_meta['ar']}", "الترتيب التالي مبني على درجات تلخص عدة مؤشرات لكل هدف، من 100:"]
                parts.extend(f"{i}. **{row['governorate']}** — {row['score']} (الترتيب {row['rank']})." for i, row in enumerate(top_rows, 1))
            else:
                parts = [f"### Highest-ranked governorates in {sdg_meta['en']}", "The ranking uses the report's composite scores out of 100:"]
                parts.extend(f"{i}. **{row['governorate']}** — {row['score']} (rank {row['rank']})." for i, row in enumerate(top_rows, 1))
            return "\n".join(parts)

        if entities["is_targets"]:
            if lang == "ar":
                return (
                    "### مستهدفات التنمية المستدامة لعام 2030\n"
                    "لكل مؤشر مستهدف خاص، وتعرض التقارير عادةً قيمته الحالية والفجوة المتبقية ومعدل التغيير المطلوب. "
                    "اذكر اسم المحافظة أو المؤشر المطلوب حتى تكون الإجابة محددة، لأن المستهدفات ليست رقمًا واحدًا لكل مصر."
                )
            return (
                "### 2030 sustainable development targets\n"
                "Each indicator has its own target, current value, and gap. Name a governorate or indicator for a specific answer; there is no single target number for all of Egypt."
            )

        text = " ".join(chunk.get("text", "") for chunk in chunks)
        topics = [
            ("الفقر", "الفقر"), ("التغذية", "التغذية"), ("الصحة", "الصحة"),
            ("التعليم", "التعليم"), ("العمل والبطالة", "البطالة"),
            ("المياه والصرف الصحي", "مياه"), ("الطاقة", "الطاقة"),
        ]
        found_topics = [label for label, keyword in topics if keyword in text]
        if lang == "ar":
            if found_topics:
                return (
                    "### ملخص ما وجدته في التقارير\n"
                    "المقاطع المتاحة تتناول: " + "، ".join(found_topics) + ".\n\n"
                    "بعض جداول PDF تظهر نصوصها وأرقامها بترتيب غير واضح عند استخراجها؛ لذلك لن أعرض مقطعًا مشوشًا أو أنسب رقمًا إلى مؤشر دون تحقق. "
                    "حدّد المحافظة أو المؤشر لأقدّم ملخصًا أدق مع المصدر."
                )
            return UNAVAILABLE_MSG_AR
        if found_topics:
            return (
                "### Summary of the retrieved reports\n"
                "The available passages cover: " + ", ".join(found_topics) + ".\n\n"
                "Some PDF tables are extracted with unclear number-to-indicator order, so I will not quote a potentially mismatched figure. "
                "Specify a governorate or indicator for a more precise, cited summary."
            )
        return UNAVAILABLE_MSG_EN

    def _call_gemini_api(self, query, chunks, entities, api_key, history=None):
        import requests
        
        context_blocks = []
        for c in chunks:
            context_blocks.append(
                f"[تقرير: {c['filename']} | المحافظة: {c['governorate_ar']} ({c['governorate_en']}) | {c['edition_name']} | صفحة: {c['page_number']} | الرابط: {c['source_url']}]\n{c['text']}"
            )
        context_str = "\n\n---\n\n".join(context_blocks)
        
        system_instruction = (
            "You are the official Egypt SDGs Knowledge Assistant (مساعد المعرفة لأهداف التنمية المستدامة في مصر), "
            "an expert AI assistant designed for official government and academic presentations.\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Answer using ONLY the official information provided in the context below.\n"
            "2. Never invent or hallucinate statistics, percentages, rankings, or dates.\n"
            "3. If sufficient information is not available in the context, explicitly say: "
            f"'{UNAVAILABLE_MSG_AR}'\n"
            "4. Clearly distinguish between the First Edition (2021) and Second Edition (2024/2025) and explain methodology differences when comparing.\n"
            "5. Include precise source citations (Report name, Governorate, Edition, Page Number, and link) for all factual claims.\n"
            "6. Support both standard Arabic and Egyptian conversational phrasing naturally. When user asks in Arabic, reply in Arabic; when in English, reply in English.\n"
            "7. Format your answer with clean Markdown, bullet points, and highlight key metrics.\n"
            "8. The retrieved context may contain PDF table text with broken column order. Never copy garbled fragments or join values with vertical bars; only state a number when it is clearly matched to its indicator.\n"
            "9. Write concise, coherent Arabic with short sentences. If a table value is ambiguous, say it cannot be verified instead of guessing."
        )
        
        prompt = f"User Question: {query}\n\nRetrieved Official Context from MPED Reports:\n{context_str}\n\nPlease generate a precise, well-structured, source-backed answer."
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1500}
        }
        
        resp = requests.post(url, json=payload, timeout=25)
        if resp.status_code == 200:
            res_json = resp.json()
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        else:
            raise Exception(f"Gemini API returned status {resp.status_code}: {resp.text}")
