import os
import sys
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from run_graphify import tokenize

def test_tokenize_thai_and_english():
    text = "ระบบ [[Agentic-Infrastructure]] ถูกสร้างขึ้นบน [[Vercel]] สำหรับ AI Agent"
    tokens = tokenize(text)
    assert "agentic" in tokens or "agentic-infrastructure" in tokens or "infrastructure" in tokens
    assert "vercel" in tokens
    assert "agent" in tokens

def test_wikilink_regex_parsing():
    sample_text = """
    นี่คือโน้ตที่มี [[Concept-A]] และ [[Concept-B|ชื่อแสดงผล]] และ [[Concept-C#หัวข้อย่อย]]
    """
    raw_links = re.findall(r'\[\[(.*?)\]\]', sample_text)
    clean_links = [l.split('|')[0].split('#')[0].strip() for l in raw_links]
    
    assert "Concept-A" in clean_links
    assert "Concept-B" in clean_links
    assert "Concept-C" in clean_links
    assert len(clean_links) == 3
