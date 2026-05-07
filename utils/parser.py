# utils/parser.py
# ─────────────────────────────────────────────────────────────────
# Reusable helpers for extracting structured data from LLM output.
# LLMs occasionally wrap JSON in markdown fences — these helpers
# handle that gracefully.
# ─────────────────────────────────────────────────────────────────
from __future__ import annotations

import json
import re
from typing import Any

from utils.logger import get_logger

log = get_logger(__name__)


def extract_json(text: str) -> dict[str, Any]:
    """
    Parse JSON from LLM text that may contain markdown fences.

    Priority:
      1. Raw JSON (starts with '{')
      2. ```json ... ``` block
      3. First '{...}' found anywhere in text

    Raises:
      ValueError if no valid JSON found.
    """
    text = text.strip()

    # 1. Already clean JSON
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # 2. Fenced JSON block
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. First { ... } pair
    brace_match = re.search(r"\{[\s\S]*\}", text)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No valid JSON found in LLM output:\n{text[:300]}")


def extract_list(text: str) -> list[str]:
    """
    Extract a flat list of strings from LLM text.

    Handles:
      - JSON arrays:  ["a", "b", "c"]
      - Numbered:     1. Item
      - Bulleted:     - Item  /  • Item  /  * Item
      - Plain lines
    """
    text = text.strip()

    # JSON array
    arr_match = re.search(r"\[[\s\S]*?\]", text)
    if arr_match:
        try:
            result = json.loads(arr_match.group())
            if isinstance(result, list):
                return [str(i).strip() for i in result if str(i).strip()]
        except json.JSONDecodeError:
            pass

    # Line-by-line parsing
    lines = text.splitlines()
    items: list[str] = []
    for line in lines:
        # Strip numbering, bullets, markdown
        cleaned = re.sub(r"^[\d]+[.)]\s*|^[-•*]\s*", "", line).strip()
        if cleaned:
            items.append(cleaned)

    return items


def safe_json(text: str, default: dict | None = None) -> dict[str, Any]:
    """Like extract_json but returns `default` instead of raising."""
    try:
        return extract_json(text)
    except ValueError:
        log.warning("Could not parse JSON — returning default")
        return default or {}