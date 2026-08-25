import os
import sys
import pytest

# เพิ่ม scripts directory ใน sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from wiki_ingest import clean_json_response, get_ingest_prompt, extract_pdf_text_fallback

def test_clean_json_response_with_markdown_fences():
    raw_response = """```json
{
  "summary": {
    "title": "ทดสอบระบบ",
    "content": "เนื้อหา"
  },
  "concepts": [],
  "entities": []
}
```"""
    data = clean_json_response(raw_response)
    assert isinstance(data, dict)
    assert data["summary"]["title"] == "ทดสอบระบบ"

def test_clean_json_response_with_plain_code_fences():
    raw_response = """```
{
  "summary": {
    "title": "Plain Code Block",
    "content": "Sample"
  }
}
```"""
    data = clean_json_response(raw_response)
    assert data["summary"]["title"] == "Plain Code Block"

def test_clean_json_response_with_surrounding_text():
    raw_response = """นี่คือผลลัพธ์การประมวลผล:
{
  "summary": {
    "title": "Embedded JSON"
  }
}
ขอบคุณที่ใช้บริการ"""
    data = clean_json_response(raw_response)
    assert data["summary"]["title"] == "Embedded JSON"

def test_clean_json_response_invalid_raises():
    with pytest.raises(ValueError):
        clean_json_response("ข้อความธรรมดาที่ไม่มี JSON เลย")

def test_get_ingest_prompt_format():
    prompt = get_ingest_prompt(raw_text="ข้อมูลทดสอบ", today_str="2026-08-25", base_name="Doc1")
    assert "Doc1" in prompt
    assert "2026-08-25" in prompt
    assert "ข้อมูลทดสอบ" in prompt

def test_extract_pdf_fallback_non_existent():
    res = extract_pdf_text_fallback("non_existent_file.pdf")
    assert "ไม่สามารถสกัดข้อความได้โดยตรง" in res or res == ""
