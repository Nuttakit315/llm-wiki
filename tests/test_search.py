import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from search_wiki import tokenize, search_wiki

def test_search_tokenize_empty():
    assert tokenize("") == []
    assert tokenize("   ") == []

def test_search_wiki_empty_query():
    results = search_wiki("")
    assert results == []

def test_search_wiki_structure(tmp_path):
    # ทดสอบว่าผลลัพธ์ที่ได้มีโครงสร้างถูกต้อง (id, path, type, score, snippet, links)
    results = search_wiki("Agent")
    if results:
        top_res = results[0]
        assert "id" in top_res
        assert "path" in top_res
        assert "score" in top_res
        assert "snippet" in top_res
        assert "links" in top_res
        assert top_res["score"] > 0
