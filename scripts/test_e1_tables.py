import pypdf

reader = pypdf.PdfReader("data/reports/edition_1/6_القاهرة.pdf")
for p in [20, 21, 22, 23]:
    print(f"\n================ Page {p} Cairo E1 ================")
    txt = reader.pages[p-1].extract_text()
    for line in txt.split("\n"):
        if any(term in line for term in ["الفقر", "التقزم", "وفيات", "الأمية", "البطالة", "تنظيم الأسرة", "معدل", "نسبة"]):
            print("  ", line)
