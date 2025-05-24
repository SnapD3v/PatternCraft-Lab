"""
Description: Provides utility functions for working with Markdown content,
including parsing and formatting operations for text content.
"""

import re


def strip_markdown(md_text: str) -> str:
    md_text = re.sub(r"[#*_`>\-\+]+", "", md_text)
    md_text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", md_text)  # ссылки
    return md_text.strip()
