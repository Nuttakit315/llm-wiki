import os
import sys
import json
import re

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
import argparse
from collections import Counter

def tokenize(text: str) -> list[str]:
    """Enhanced Thai & Multilingual Tokenizer for Search Query"""
    text = text.lower()
    text = re.sub(r'\[\[(.*?)\]\]', r'\1', text)
    text = re.sub(r'[#*`_~>\-\[\]\(\)\{\}\:\.\,\!\?]', ' ', text)
    
    raw_tokens = re.findall(r'[\u0E00-\u0E7Fa-zA-Z0-9_]+', text)
    tokens = []

    for t in raw_tokens:
        if len(t) <= 1:
            continue
        tokens.append(t)
        if re.search(r'[\u0E00-\u0E7F]', t) and len(t) > 4:
            for n in [3, 4]:
                for i in range(len(t) - n + 1):
                    tokens.append(t[i:i+n])

    return tokens

def search_wiki(query: str, top_k: int = 5, index_path: str = "graph/search_index.json") -> list[dict]:
    """ค้นหาความรู้ในคลังด้วย Hybrid Lexical Matching, TF-IDF Scores และ Graph Centrality"""
    if not os.path.exists(index_path):
        if index_path == "graph/search_index.json":
            print("⚠️ ไม่พบไฟล์ดัชนี graph/search_index.json กำลังสร้างดัชนี...")
            import subprocess
            try:
                subprocess.run(["python", "scripts/run_graphify.py"], check=True)
            except Exception:
                pass

    if not os.path.exists(index_path):
        print("❌ ไม่พบไฟล์ดัชนีการสืบค้น")
        return []

    with open(index_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    query_tokens = tokenize(query)
    if not query_tokens:
        print("⚠️ ไม่พบคำค้นหาที่ถูกต้อง")
        return []

    q_counts = Counter(query_tokens)
    scored_results = []

    for doc in data.get("documents", []):
        score = 0.0
        doc_id = doc.get("id", "")
        doc_id_lower = doc_id.lower()
        doc_title_lower = doc.get("title", "").lower()
        doc_snippet_lower = doc.get("snippet", "").lower()
        doc_tfidf = doc.get("tfidf", {})
        doc_tokens = doc.get("tokens", {})

        # 1. Exact Title & Substring Match Bonus
        for qt in query_tokens:
            if qt in doc_id_lower or qt in doc_title_lower:
                score += 4.0
            if qt in doc_snippet_lower:
                score += 1.5

        # 2. Token / TF-IDF Weight
        for token, count in q_counts.items():
            if token in doc_tfidf:
                score += doc_tfidf[token] * count * 3.0
            elif token in doc_tokens:
                score += doc_tokens[token] * count * 2.0

        # 3. Knowledge Graph Link Connectivity Bonus
        links = doc.get("links", [])
        score += len(links) * 0.08

        if score > 0.05:
            scored_results.append({
                "id": doc_id,
                "path": doc.get("path", "").replace("\\", "/"),
                "title": doc.get("title", doc_id),
                "type": doc.get("type", "Document"),
                "score": round(score, 2),
                "snippet": doc.get("snippet", ""),
                "links": links[:6]
            })

    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results[:top_k]

def format_search_results(query: str, results: list[dict]):
    print(f"\n🔎 ผลการสืบค้น (Hybrid Lexical & Graph Search) สำหรับ: \"{query}\" (พบ {len(results)} รายการ)")
    print("=" * 70)

    if not results:
        print("❌ ไม่พบเนื้อหาที่ตรงกับคำค้นหาในคลังความรู้")
        return

    for idx, r in enumerate(results, 1):
        type_icon = "📄"
        if r["type"] == "Concept":
            type_icon = "🧠"
        elif r["type"] == "Entity":
            type_icon = "🏛️"
        elif r["type"] == "Synthesis":
            type_icon = "💡"

        links_str = ", ".join([f"[[{l}]]" for l in r["links"]]) if r["links"] else "*(ไม่มี)*"
        print(f"{idx}. {type_icon} [{r['type']}] [[{r['id']}]]  (Score: {r['score']})")
        print(f"   📂 File: {r['path']}")
        print(f"   📝 Snippet: {r['snippet']}")
        print(f"   🔗 Connected Nodes: {links_str}")
        print("-" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal LLM Wiki Hybrid Lexical & Graph Search Engine")
    parser.add_argument("query", nargs="*", help="คำหรือประโยคที่ต้องการค้นหา")
    parser.add_argument("--top", type=int, default=5, help="จำนวนผลลัพธ์ที่ต้องการ (ค่าเริ่มต้น 5)")
    args = parser.parse_args()

    query_str = " ".join(args.query).strip()
    if not query_str:
        query_str = input("🔍 ป้อนคำหรือหัวข้อที่ต้องการค้นหา: ").strip()

    if query_str:
        results = search_wiki(query_str, top_k=args.top)
        format_search_results(query_str, results)
    else:
        print("กรุณาระบุคำค้นหา เช่น: python scripts/search_wiki.py 'Agentic'")
