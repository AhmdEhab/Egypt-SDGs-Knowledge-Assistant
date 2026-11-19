import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.rag_engine import RAGEngine

def run_tests():
    engine = RAGEngine()
    
    test_queries = [
        "ما هو وضع محافظة الغربية في تحقيق أهداف التنمية المستدامة؟",
        "قارن أداء محافظة القاهرة ومحافظة الإسكندرية.",
        "ما هي أهم المؤشرات التي تحتاج إلى تحسين في محافظة البحيرة؟",
        "ما هو أداء المحافظات في الهدف الرابع الخاص بالتعليم؟",
        "هل حصل تحسن بين الإصدار الأول والإصدار الثاني في الغربية؟",
        "What are the main sustainable development challenges in Gharbia?",
        "Compare the performance of Cairo and Alexandria.",
        "ما هي تفاصيل برنامج رحلات الفضاء إلى كوكب المريخ؟"
    ]
    
    print("\n================ RUNNING RAG ENGINE EVALUATION ================\n")
    for q in test_queries:
        print(f"\n--- QUERY: {q} ---")
        res = engine.generate_response(q)
        print("ANSWER PREVIEW:\n", res["answer"][:400], "...\n")
        print(f"CITATIONS ({len(res['citations'])}):")
        for c in res["citations"][:3]:
            print(f"  - [{c['edition_name']}] {c['report_name']} (Page {c['page_number']})")
        if res.get("table"):
            print("  [HAS STRUCTURED COMPARISON TABLE]")
        if res.get("chart"):
            print("  [HAS INTERACTIVE CHART DATA]")
            
if __name__ == "__main__":
    run_tests()
