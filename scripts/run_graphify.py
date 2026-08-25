import os
import sys
import json
import glob
import re
import math
from collections import Counter

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def tokenize(text: str) -> list[str]:
    """
    Enhanced Thai & Multilingual Tokenizer:
    1. ตัด Markdown tags และ Wikilinks
    2. ทำความสะอาดเครื่องหมายพิเศษ
    3. หากมีคำภาษาไทยยาวๆ (>4 ตัวอักษร) จะสกัด Sub-words / N-grams ช่วยให้ค้นหาภาษาไทยได้ครอบคลุม
    """
    text = text.lower()
    text = re.sub(r'\[\[(.*?)\]\]', r'\1', text)
    text = re.sub(r'[#*`_~>\-\[\]\(\)\{\}\:\.\,\!\?]', ' ', text)
    
    # สกัดคำภาษาอังกฤษ ตัวเลข และคำภาษาไทย
    raw_tokens = re.findall(r'[\u0E00-\u0E7Fa-zA-Z0-9_]+', text)
    tokens = []

    for t in raw_tokens:
        if len(t) <= 1:
            continue
        tokens.append(t)
        
        # สำหรับคำภาษาไทยที่ติดกันเป็นพวงยาวๆ (>6 ตัวอักษร) สกัด 3-gram และ 4-gram เสริม
        if re.search(r'[\u0E00-\u0E7F]', t) and len(t) > 6:
            for n in [3, 4, 5]:
                for i in range(len(t) - n + 1):
                    sub = t[i:i+n]
                    tokens.append(sub)

    return tokens

def build_knowledge_graph_and_search_index():
    wiki_files = glob.glob("wiki/**/*.md", recursive=True) + glob.glob("wiki/*.md")
    wiki_files = list(set([f for f in wiki_files if not os.path.basename(f).startswith(".")]))
    
    nodes = []
    edges = []
    seen_nodes = set()
    node_degree = Counter()
    
    documents_index = []
    all_doc_tokens = []
    doc_freq = Counter()

    print(f"🔍 เริ่มสแกนไฟล์ Markdown ใน wiki/ ทั้งหมด {len(wiki_files)} ไฟล์...")

    for file_path in wiki_files:
        doc_name = os.path.splitext(os.path.basename(file_path))[0]
        clean_path = file_path.replace("\\", "/")
        
        doc_type = "Document"
        if "/concepts/" in clean_path:
            doc_type = "Concept"
        elif "/entities/" in clean_path:
            doc_type = "Entity"
        elif "/summaries/" in clean_path:
            doc_type = "Summary"
        elif "/synthesis/" in clean_path:
            doc_type = "Synthesis"

        if doc_name not in seen_nodes:
            nodes.append({
                "id": doc_name,
                "label": doc_name,
                "type": doc_type,
                "path": clean_path
            })
            seen_nodes.add(doc_name)

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception as e:
            print(f"⚠️ ไม่สามารถอ่านไฟล์ {file_path}: {e}")
            continue

        raw_links = re.findall(r'\[\[(.*?)\]\]', text)
        doc_out_links = []
        for link in raw_links:
            clean_link = link.split("|")[0].split("#")[0].strip()
            if not clean_link or clean_link == doc_name:
                continue

            if clean_link not in seen_nodes:
                nodes.append({
                    "id": clean_link,
                    "label": clean_link,
                    "type": "Concept"
                })
                seen_nodes.add(clean_link)

            edges.append({
                "source": doc_name,
                "target": clean_link,
                "relation": "links_to"
            })
            node_degree[doc_name] += 1
            node_degree[clean_link] += 1
            doc_out_links.append(clean_link)

        clean_preview = re.sub(r'---[\s\S]*?---', '', text).strip()
        snippet = clean_preview[:250].replace("\n", " ").strip() + "..." if len(clean_preview) > 250 else clean_preview

        tokens = tokenize(text)
        token_counts = Counter(tokens)
        unique_tokens = set(tokens)
        for t in unique_tokens:
            doc_freq[t] += 1

        documents_index.append({
            "id": doc_name,
            "path": clean_path,
            "type": doc_type,
            "snippet": snippet,
            "links": doc_out_links,
            "token_counts": token_counts,
            "total_tokens": len(tokens)
        })
        all_doc_tokens.append(tokens)

    for node in nodes:
        node["degree"] = node_degree[node["id"]]

    os.makedirs("graph", exist_ok=True)

    # 1. บันทึก Knowledge Graph
    graph_data = {
        "metadata": {
            "engine": "Universal LLM Wiki Knowledge Graph",
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        },
        "nodes": nodes,
        "edges": edges
    }
    with open("graph/graph.json", "w", encoding="utf-8") as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=2)

    # 2. บันทึก Hybrid Lexical & TF-IDF Graph Search Index
    num_docs = max(1, len(documents_index))
    search_docs = []
    for doc in documents_index:
        tfidf = {}
        for token, count in doc["token_counts"].items():
            tf = count / max(1, doc["total_tokens"])
            idf = math.log((num_docs + 1) / (doc_freq[token] + 1)) + 1
            tfidf[token] = round(tf * idf, 4)

        search_docs.append({
            "id": doc["id"],
            "path": doc["path"],
            "type": doc["type"],
            "snippet": doc["snippet"],
            "links": doc["links"],
            "tfidf": tfidf
        })

    search_index_data = {
        "metadata": {
            "engine": "Hybrid Lexical & TF-IDF Graph Search Index",
            "total_documents": len(search_docs),
            "total_terms": len(doc_freq)
        },
        "documents": search_docs
    }
    with open("graph/search_index.json", "w", encoding="utf-8") as f:
        json.dump(search_index_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Knowledge Graph & Search Indexing เสร็จสมบูรณ์!")
    print(f"   📊 โหนดทั้งหมด (Nodes): {len(nodes)}")
    print(f"   🔗 เส้นเชื่อมทั้งหมด (Edges): {len(edges)}")
    print(f"   🔎 ดัชนีสืบค้น Hybrid Index: graph/search_index.json ({len(search_docs)} เอกสาร)")

if __name__ == "__main__":
    build_knowledge_graph_and_search_index()
