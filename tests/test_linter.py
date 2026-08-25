import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from lint_wiki import parse_frontmatter, lint_knowledge_base

def test_parse_valid_frontmatter():
    sample_md = """---
type: concept
created: 2026-08-25
updated: 2026-08-25
tags:
  - ai
  - km
sources:
  - "[[SourceA]]"
---
# Content Title"""
    fm = parse_frontmatter(sample_md)
    assert fm["type"] == "concept"
    assert fm["created"] == "2026-08-25"
    assert "ai" in fm["tags"]
    assert "[[SourceA]]" in fm["sources"]

def test_parse_empty_or_no_frontmatter():
    assert parse_frontmatter("# No Frontmatter") == {}
    assert parse_frontmatter("") == {}

def test_lint_knowledge_base_runs():
    # ตรวจสอบว่า Linter ทำงานได้โดยไม่เกิด Unhandled Exception
    success = lint_knowledge_base(auto_repair=False, strict=False)
    assert success in [True, False]
