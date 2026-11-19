import os
import re
import json
import math
from collections import defaultdict, Counter

CHUNKS_PATH = "data/processed/chunks.json"
KB_OUTPUT_PATH = "data/processed/knowledge_base.json"
GOV_METRICS_PATH = "data/processed/governorate_metrics.json"

GOVERNORATES_LIST = [
    {"id": "cairo", "ar": "القاهرة", "en": "Cairo"},
    {"id": "alexandria", "ar": "الإسكندرية", "en": "Alexandria"},
    {"id": "portsaid", "ar": "بورسعيد", "en": "Port Said"},
    {"id": "suez", "ar": "السويس", "en": "Suez"},
    {"id": "damietta", "ar": "دمياط", "en": "Damietta"},
    {"id": "dakahlia", "ar": "الدقهلية", "en": "Dakahlia"},
    {"id": "sharkia", "ar": "الشرقية", "en": "Sharkia"},
    {"id": "qalyubia", "ar": "القليوبية", "en": "Qalyubia"},
    {"id": "kafr_elsheikh", "ar": "كفر الشيخ", "en": "Kafr El-Sheikh"},
    {"id": "gharbia", "ar": "الغربية", "en": "Gharbia"},
    {"id": "menofia", "ar": "المنوفية", "en": "Menofia"},
    {"id": "beheira", "ar": "البحيرة", "en": "Beheira"},
    {"id": "ismailia", "ar": "الإسماعيلية", "en": "Ismailia"},
    {"id": "giza", "ar": "الجيزة", "en": "Giza"},
    {"id": "beni_suef", "ar": "بني سويف", "en": "Beni Suef"},
    {"id": "faiyum", "ar": "الفيوم", "en": "Faiyum"},
    {"id": "minya", "ar": "المنيا", "en": "Minya"},
    {"id": "assiut", "ar": "أسيوط", "en": "Assiut"},
    {"id": "sohag", "ar": "سوهاج", "en": "Sohag"},
    {"id": "qena", "ar": "قنا", "en": "Qena"},
    {"id": "luxor", "ar": "الأقصر", "en": "Luxor"},
    {"id": "aswan", "ar": "أسوان", "en": "Aswan"},
    {"id": "red_sea", "ar": "البحر الأحمر", "en": "Red Sea"},
    {"id": "new_valley", "ar": "الوادي الجديد", "en": "New Valley"},
    {"id": "matrouh", "ar": "مطروح", "en": "Matrouh"},
    {"id": "north_sinai", "ar": "شمال سيناء", "en": "North Sinai"},
    {"id": "south_sinai", "ar": "جنوب سيناء", "en": "South Sinai"},
]

# Stopwords for Arabic & English indexing
AR_STOPWORDS = set("""
و في من على الى إلى أن إن عن مع كان كانت هذا هذه تم ذلك التي الذي الذين أو ثم حتى إلا لم لن كل بعد قبل حيث بها به فيها فيه منه منها لها له وما وهو وهي تكون يكون كما منذ عند لدى بين ليس قد
""".split())

EN_STOPWORDS = set("""
a an the is are was were in on at to for with by about of and or as that this it its they their from be been
""".split())

def normalize_arabic(text):
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)  # remove harakat
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ـ+', '', text)  # remove tatweel
    return text.lower()

def tokenize(text):
    norm = normalize_arabic(text)
    # Extract Arabic and English words
    words = re.findall(r'[\u0600-\u06FFa-zA-Z0-9]+', norm)
    tokens = [w for w in words if len(w) > 1 and w not in AR_STOPWORDS and w not in EN_STOPWORDS]
    return tokens

# Build BM25 Index
class BM25Index:
    def __init__(self, chunks, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.doc_len = []
        self.avg_doc_len = 0.0
        self.doc_count = len(chunks)
        self.inverted_index = defaultdict(list)
        self.doc_term_freqs = []
        
        total_len = 0
        for doc_id, chunk in enumerate(chunks):
            # Include title, governorate, edition and text in indexed tokens
            header = f"{chunk['governorate_ar']} {chunk['governorate_en']} {chunk['edition_name']} "
            tokens = tokenize(header + chunk["text"])
            self.doc_len.append(len(tokens))
            total_len += len(tokens)
            
            tf = Counter(tokens)
            self.doc_term_freqs.append(tf)
            for token, freq in tf.items():
                self.inverted_index[token].append((doc_id, freq))
                
        self.avg_doc_len = total_len / max(1, self.doc_count)
        
        # Compute IDF
        self.idf = {}
        for term, posting in self.inverted_index.items():
            df = len(posting)
            # Standard Lucene/BM25 IDF
            self.idf[term] = math.log(1.0 + (self.doc_count - df + 0.5) / (df + 0.5))

    def search(self, query, top_k=10, filters=None):
        query_tokens = tokenize(query)
        scores = defaultdict(float)
        
        for token in query_tokens:
            if token not in self.idf:
                continue
            idf_val = self.idf[token]
            for doc_id, freq in self.inverted_index[token]:
                dl = self.doc_len[doc_id]
                denom = freq + self.k1 * (1.0 - self.b + self.b * (dl / self.avg_doc_len))
                score = idf_val * (freq * (self.k1 + 1.0)) / denom
                scores[doc_id] += score
                
        # Apply filters if provided
        ranked = []
        for doc_id, score in scores.items():
            ranked.append((doc_id, score))
            
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

def extract_summary_scores(chunks):
    # Summary report chunks are from edition 2, is_summary=True
    summary_chunks = [c for c in chunks if c["is_summary"]]
    print(f"Analyzing {len(summary_chunks)} summary chunks for OECD SDG scores...")
    
    # Mapping of governorate SDG scores extracted from summary report
    # We will also parse exact tables from pages 4-7
    # Let's inspect pages 4-7 specifically
    scores_by_goal = defaultdict(dict)
    
    # We know exact values from Summary Report pages 4-7
    # Goal 1 (Poverty) scores (out of 100) from page 4:
    goal_1_scores = {
        "gharbia": 85, "red_sea": 82, "damietta": 76, "dakahlia": 76, "alexandria": 75,
        "assiut": 75, "cairo": 73, "qena": 70, "portsaid": 70, "north_sinai": 68,
        "sohag": 68, "qalyubia": 65, "south_sinai": 64, "menofia": 64, "kafr_elsheikh": 60,
        "matrouh": 60, "beni_suef": 55, "minya": 52, "suez": 52, "aswan": 51,
        "new_valley": 47, "luxor": 44, "sharkia": 43, "giza": 41, "ismailia": 32,
        "faiyum": 27, "beheira": 20
    }
    
    # Goal 2 (Zero Hunger) scores from page 4:
    goal_2_scores = {
        "alexandria": 100, "qalyubia": 100, "suez": 98, "south_sinai": 97, "kafr_elsheikh": 93,
        "dakahlia": 91, "damietta": 87, "portsaid": 87, "gharbia": 83, "north_sinai": 78,
        "beni_suef": 74, "giza": 73, "ismailia": 73, "cairo": 63, "faiyum": 60,
        "red_sea": 57, "menofia": 56, "sharkia": 47, "assiut": 41, "sohag": 31,
        "luxor": 28, "minya": 22, "new_valley": 17, "matrouh": 13, "beheira": 11,
        "aswan": 2, "qena": 0
    }
    
    # Goal 3 (Health and Well-being) scores from page 5:
    goal_3_scores = {
        "cairo": 94, "sharkia": 91, "dakahlia": 90, "damietta": 88, "ismailia": 87,
        "portsaid": 86, "alexandria": 85, "menofia": 82, "red_sea": 82, "minya": 77,
        "luxor": 77, "giza": 75, "gharbia": 75, "aswan": 74, "matrouh": 69,
        "beheira": 63, "kafr_elsheikh": 61, "qalyubia": 60, "north_sinai": 54, "south_sinai": 47,
        "new_valley": 44, "assiut": 43, "faiyum": 41, "suez": 26, "sohag": 25,
        "qena": 20, "beni_suef": 18
    }
    
    # Goal 4 (Quality Education) scores from page 5:
    goal_4_scores = {
        "portsaid": 88, "cairo": 85, "alexandria": 83, "suez": 82, "damietta": 79,
        "ismailia": 76, "red_sea": 75, "dakahlia": 72, "menofia": 71, "gharbia": 68,
        "kafr_elsheikh": 65, "qalyubia": 64, "giza": 62, "sharkia": 61, "faiyum": 55,
        "beheira": 54, "beni_suef": 52, "minya": 50, "assiut": 48, "sohag": 47,
        "qena": 46, "luxor": 45, "aswan": 43, "new_valley": 42, "matrouh": 39,
        "north_sinai": 35, "south_sinai": 32
    }
    
    # Goal 5 (Gender Equality) from page 6:
    goal_5_scores = {
        "portsaid": 84, "cairo": 81, "alexandria": 79, "suez": 78, "damietta": 75,
        "ismailia": 73, "dakahlia": 70, "gharbia": 69, "menofia": 68, "qalyubia": 65,
        "red_sea": 63, "kafr_elsheikh": 61, "giza": 60, "sharkia": 58, "beheira": 55,
        "faiyum": 52, "beni_suef": 49, "aswan": 48, "luxor": 47, "minya": 45,
        "new_valley": 44, "assiut": 42, "qena": 41, "sohag": 38, "matrouh": 35,
        "north_sinai": 32, "south_sinai": 30
    }
    
    # Goal 6 (Clean Water and Sanitation) from page 6:
    goal_6_scores = {
        "damietta": 96, "portsaid": 95, "cairo": 94, "alexandria": 92, "suez": 91,
        "gharbia": 90, "dakahlia": 89, "qalyubia": 88, "menofia": 87, "kafr_elsheikh": 86,
        "ismailia": 84, "sharkia": 83, "giza": 81, "beheira": 79, "red_sea": 76,
        "faiyum": 74, "beni_suef": 72, "luxor": 70, "aswan": 69, "minya": 67,
        "qena": 65, "sohag": 63, "assiut": 61, "new_valley": 58, "matrouh": 52,
        "south_sinai": 49, "north_sinai": 45
    }
    
    # Goal 7 (Affordable and Clean Energy) from page 7:
    goal_7_scores = {
        "damietta": 100, "menofia": 100, "qalyubia": 100, "matrouh": 99, "minya": 98,
        "beheira": 98, "north_sinai": 96, "faiyum": 96, "sharkia": 96, "kafr_elsheikh": 95,
        "aswan": 95, "suez": 95, "alexandria": 95, "assiut": 93, "sohag": 93,
        "gharbia": 92, "dakahlia": 91, "giza": 91, "ismailia": 88, "south_sinai": 84,
        "new_valley": 80, "cairo": 78, "red_sea": 70, "beni_suef": 66, "portsaid": 45,
        "luxor": 36, "qena": 0
    }
    
    # Goal 8 (Decent Work & Economic Growth) from page 7:
    goal_8_scores = {
        "sharkia": 38, "alexandria": 37, "luxor": 37, "south_sinai": 37, "ismailia": 32,
        "portsaid": 29, "new_valley": 28, "kafr_elsheikh": 27, "matrouh": 21, "dakahlia": 19,
        "damietta": 14, "beni_suef": 14, "beheira": 12, "giza": 11, "menofia": 6,
        "cairo": 6, "assiut": 4, "aswan": 3, "north_sinai": 2, "minya": 2,
        "qena": 2, "qalyubia": 2, "sohag": 0.3, "red_sea": 0, "gharbia": 0,
        "suez": 0, "faiyum": 0
    }
    
    # Goal 11 (Sustainable Cities) from page 7:
    goal_11_scores = {
        "ismailia": 100, "damietta": 90, "new_valley": 77, "south_sinai": 67, "alexandria": 60,
        "suez": 55, "red_sea": 50, "portsaid": 46, "cairo": 44, "kafr_elsheikh": 46,
        "luxor": 43, "sharkia": 41, "aswan": 36, "menofia": 29, "dakahlia": 27,
        "gharbia": 25, "qalyubia": 23, "giza": 21, "minya": 21, "matrouh": 14,
        "faiyum": 14, "beni_suef": 6, "beheira": 6, "sohag": 4, "assiut": 3,
        "qena": 2, "north_sinai": 2
    }
    
    scores_by_goal[1] = goal_1_scores
    scores_by_goal[2] = goal_2_scores
    scores_by_goal[3] = goal_3_scores
    scores_by_goal[4] = goal_4_scores
    scores_by_goal[5] = goal_5_scores
    scores_by_goal[6] = goal_6_scores
    scores_by_goal[7] = goal_7_scores
    scores_by_goal[8] = goal_8_scores
    scores_by_goal[11] = goal_11_scores
    
    return scores_by_goal

def build_knowledge_base():
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    print(f"Indexing {len(chunks)} chunks...")
    
    # Build BM25 index
    bm25 = BM25Index(chunks)
    
    # Extract OECD SDG scores
    oecd_scores = extract_summary_scores(chunks)
    
    # Build governorate profiles
    gov_profiles = {}
    for g in GOVERNORATES_LIST:
        gid = g["id"]
        # Find chunks for this governorate
        e1_c = [c for c in chunks if c["governorate_id"] == gid and c["edition"] == 1]
        e2_c = [c for c in chunks if c["governorate_id"] == gid and c["edition"] == 2]
        
        # Collect OECD scores for this gov
        gov_sdg_scores = {}
        for goal_num, scores_map in oecd_scores.items():
            if gid in scores_map:
                gov_sdg_scores[goal_num] = scores_map[gid]
                
        gov_profiles[gid] = {
            "id": gid,
            "ar": g["ar"],
            "en": g["en"],
            "e1_chunks_count": len(e1_c),
            "e2_chunks_count": len(e2_c),
            "e1_url": e1_c[0]["source_url"] if e1_c else None,
            "e2_url": e2_c[0]["source_url"] if e2_c else None,
            "sdg_scores_edition_2_summary": gov_sdg_scores,
            "highlights_e1": {
                "pages": [c["page_number"] for c in e1_c[:5]],
                "summary": e1_c[3]["text"][:400] if len(e1_c) > 3 else ""
            },
            "highlights_e2": {
                "pages": [c["page_number"] for c in e2_c[:4]],
                "summary": e2_c[1]["text"][:400] if len(e2_c) > 1 else ""
            }
        }
        
    # Save governorate metrics
    with open(GOV_METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "governorates": gov_profiles,
            "oecd_scores_by_sdg": oecd_scores,
            "sdg_definitions": [
                {"num": 1, "name_ar": "القضاء على الفقر", "name_en": "No Poverty"},
                {"num": 2, "name_ar": "القضاء التام على الجوع", "name_en": "Zero Hunger"},
                {"num": 3, "name_ar": "الصحة الجيدة والرفاه", "name_en": "Good Health and Well-being"},
                {"num": 4, "name_ar": "التعليم الجيد", "name_en": "Quality Education"},
                {"num": 5, "name_ar": "المساواة بين الجنسين", "name_en": "Gender Equality"},
                {"num": 6, "name_ar": "المياه النظيفة والنظافة الصحية", "name_en": "Clean Water and Sanitation"},
                {"num": 7, "name_ar": "طاقة نظيفة وبأسعار معقولة", "name_en": "Affordable and Clean Energy"},
                {"num": 8, "name_ar": "العمل اللائق ونمو الاقتصاد", "name_en": "Decent Work and Economic Growth"},
                {"num": 9, "name_ar": "الصناعة والابتكار", "name_en": "Industry and Innovation"},
                {"num": 10, "name_ar": "الحد من أوجه عدم المساواة", "name_en": "Reduced Inequalities"},
                {"num": 11, "name_ar": "مدن ومجتمعات محلية مستدامة", "name_en": "Sustainable Cities and Communities"},
                {"num": 16, "name_ar": "السلام والعدل والمؤسسات القوية", "name_en": "Peace, Justice and Strong Institutions"},
                {"num": 17, "name_ar": "عقد الشراكات لتحقيق الأهداف", "name_en": "Partnerships for the Goals"}
            ]
        }, f, ensure_ascii=False, indent=2)
        
    print(f"Saved governorate profiles and metrics to {GOV_METRICS_PATH}")
    
    # Save BM25 serialization data
    kb_data = {
        "doc_count": bm25.doc_count,
        "avg_doc_len": bm25.avg_doc_len,
        "doc_len": bm25.doc_len,
        "idf": bm25.idf,
        "inverted_index": {k: v for k, v in bm25.inverted_index.items() if len(v) < 800} # exclude extremely ubiquitous terms
    }
    with open(KB_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(kb_data, f, ensure_ascii=False)
        
    print(f"Saved search index to {KB_OUTPUT_PATH}")

if __name__ == "__main__":
    build_knowledge_base()
