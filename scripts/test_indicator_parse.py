import json
import re

with open("data/processed/chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Loaded {len(chunks)} chunks.")

# Test finding indicators in Edition 2 chunks
e2_chunks = [c for c in chunks if c["edition"] == 2 and not c["is_summary"]]
print(f"Edition 2 chunks: {len(e2_chunks)}")

sample_indicators = []
for c in e2_chunks[:10]:
    lines = [l.strip() for l in c["text"].split("\n") if l.strip()]
    # look for indicator lines
    for i, line in enumerate(lines):
        if any(term in line for term in ["معدل", "نسبة", "عدد", "الفقر", "الأمية", "البطالة", "الإنجاب", "وفيات"]):
            sample_indicators.append({
                "gov": c["governorate_ar"],
                "page": c["page_number"],
                "line": line,
                "context": lines[max(0, i-1):min(len(lines), i+6)]
            })

print(f"Sample indicators found: {len(sample_indicators)}")
for item in sample_indicators[:8]:
    print(f"\n[{item['gov']} p.{item['page']}] Line: {item['line']}")
    print("  Context:", " // ".join(item["context"]))
