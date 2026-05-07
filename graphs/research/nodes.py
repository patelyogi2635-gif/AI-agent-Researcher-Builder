# graphs/research/nodes.py
# -----------------------------------------------------------------
# Research Graph — 7 nodes
#
# Flow:
#   sub_planner   → refines search queries from the PlanStep
#   searcher      → Tavily (primary) + DuckDuckGo (fallback)
#   scraper       → BeautifulSoup4 fetches full page content
#   analyser      → LLM synthesises all content into insights
#   memory_writer → saves findings to ChromaDB vector store
#   reviewer      → checks quality, loops back if gaps found
#   reporter      → formats final ResearchReport
# -----------------------------------------------------------------
from __future__ import annotations

import hashlib
import time
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from langchain_groq import ChatGroq

from config import get_settings
from state import MasterState, PlanStep, ResearchReport
from utils import extract_list, get_logger, safe_json

log      = get_settings  # lazy — see _settings() below
settings = get_settings()


def _settings():
    return get_settings()


def _llm() -> ChatGroq:
    s = _settings()
    return ChatGroq(
        model=s.llm_model,
        temperature=s.llm_temperature,
        api_key=s.groq_api_key,
    )


# -----------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------

def _current_step(state: MasterState) -> PlanStep | None:
    """Return the PlanStep the research graph is currently working on."""
    plan    = state.get("execution_plan", [])
    current = state.get("current_research_step", 0)
    if current < len(plan):
        return plan[current]
    return None


def _make_memory_key(topic: str, step: int) -> str:
    h = hashlib.md5(f"{topic}_{step}".encode()).hexdigest()[:8]
    return f"research_{step}_{h}"


def _is_valid_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


# -----------------------------------------------------------------
# NODE 1 — Sub-Planner
# Refines the PlanStep's search queries into sharp, targeted ones.
# -----------------------------------------------------------------
def sub_planner(state: MasterState) -> dict[str, Any]:
    log = get_logger(__name__)

    # ── Read topic directly from state (set by main.py per step) ──
    topic   = state.get("current_topic", "") or state.get("research_topic", "unknown topic")
    queries = state.get("current_search_queries", [])

    log.info(f"[Research] sub_planner — topic: '{topic[:60]}'")

    prompt = f"""Generate 3 specific web search queries for researching this topic.

Topic: "{topic}"

Rules:
- Each query must be a different angle: overview, technical depth, latest trends
- Keep each under 10 words
- Return ONLY a JSON list: ["query 1", "query 2", "query 3"]"""

    try:
        resp    = _llm().invoke(prompt)
        refined = extract_list(resp.content)
        all_queries = list(dict.fromkeys(queries + refined))[:5]
    except Exception as e:
        log.warning(f"[Research] sub_planner LLM failed: {e}")
        all_queries = queries or [topic]

    log.info(f"[Research] sub_planner: {len(all_queries)} queries ready")
    return {
        "current_search_queries": all_queries,
        "current_topic":          topic,
        "review_iteration":       0,
    }


# -----------------------------------------------------------------
# NODE 2 — Searcher
# Tavily (primary) → DuckDuckGo (fallback) → combine results
# -----------------------------------------------------------------
def searcher(state: MasterState) -> dict[str, Any]:
    log = get_logger(__name__)
    queries = state.get("current_search_queries", [])
    results = []

    for query in queries:
        # ── Try Tavily ─────────────────────────────────────────────
        tavily_key = _settings().tavily_api_key
        if tavily_key and not tavily_key.startswith("tvly_your"):
            try:
                from tavily import TavilyClient
                hits = TavilyClient(api_key=tavily_key).search(
                    query=query, max_results=_settings().max_search_results
                ).get("results", [])
                for h in hits:
                    results.append({
                        "url":     h.get("url", ""),
                        "title":   h.get("title", ""),
                        "snippet": h.get("content", ""),
                        "source":  "tavily",
                    })
                log.info(f"[Research] Tavily: {len(hits)} hits for '{query[:40]}'")
                continue
            except Exception as e:
                log.warning(f"[Research] Tavily failed: {e}")

        # ── Fallback: DuckDuckGo DDGS (new API) ───────────────────
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                hits = list(ddgs.text(query, max_results=4))
            for h in hits:
                results.append({
                    "url":     h.get("href", ""),
                    "title":   h.get("title", ""),
                    "snippet": h.get("body", ""),
                    "source":  "duckduckgo",
                })
            log.info(f"[Research] DDG: {len(hits)} hits for '{query[:40]}'")
        except Exception as e:
            log.warning(f"[Research] DDG also failed: {e} — will use LLM knowledge")

    # Deduplicate
    seen, unique = set(), []
    for r in results:
        key = r["url"] or r["snippet"][:60]
        if key not in seen:
            seen.add(key)
            unique.append(r)

    log.info(f"[Research] searcher total: {len(unique)} unique results")
    return {"search_results": unique}


# -----------------------------------------------------------------
# NODE 3 — Scraper
# Fetches full text from top URLs using requests + BeautifulSoup4
# -----------------------------------------------------------------
def scraper(state: MasterState) -> dict[str, Any]:
    log = get_logger(__name__)
    log.info("[Research] scraper started")

    results  = state.get("search_results", [])
    max_pages = _settings().max_scrape_pages
    timeout   = _settings().scrape_timeout_secs
    scraped   = []

    # Only scrape results that have a real URL
    scrapeable = [r for r in results if _is_valid_url(r.get("url", ""))][:max_pages]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    for item in scrapeable:
        url = item["url"]
        try:
            resp = requests.get(url, timeout=timeout, headers=headers)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            # Remove noise tags
            for tag in soup(["script", "style", "nav", "footer",
                              "header", "aside", "form", "iframe"]):
                tag.decompose()

            # Extract clean text — prioritise article/main content
            content = ""
            for selector in ["article", "main", ".content",
                              "#content", ".post-content"]:
                el = soup.select_one(selector)
                if el:
                    content = el.get_text(separator=" ", strip=True)
                    break
            if not content:
                content = soup.get_text(separator=" ", strip=True)

            # Normalise whitespace and cap length
            content = " ".join(content.split())[:4000]

            if len(content) > 100:
                scraped.append({
                    "url":     url,
                    "title":   item.get("title", ""),
                    "content": content,
                })
                log.info(f"[Research] Scraped {len(content)} chars from {url[:60]}")

            time.sleep(0.3)  # polite crawl delay

        except Exception as e:
            log.warning(f"[Research] Could not scrape {url[:60]}: {e}")

    # For DDG results with no URL, include snippet as scraped content
    for item in results:
        if not _is_valid_url(item.get("url", "")) and item.get("snippet"):
            scraped.append({
                "url":     "duckduckgo_search",
                "title":   item.get("title", ""),
                "content": item["snippet"],
            })

    log.info(f"[Research] scraper: {len(scraped)} pages successfully scraped")
    return {"scraped_content": scraped}


# -----------------------------------------------------------------
# NODE 4 — Analyser
# LLM synthesises all scraped content into structured insights
# -----------------------------------------------------------------
def analyser(state: MasterState) -> dict[str, Any]:
    log = get_logger(__name__)
    topic   = state.get("current_topic", state.get("research_topic", ""))
    scraped = state.get("scraped_content", [])
    results = state.get("search_results", [])

    # Build context from scraped + snippets
    parts = []
    for item in scraped[:5]:
        parts.append(f"[Source: {item.get('url','unknown')}]\n{item['content'][:2000]}")

    scraped_urls = {s["url"] for s in scraped}
    for r in results:
        if r.get("url","") not in scraped_urls and r.get("snippet",""):
            parts.append(f"[Snippet]\n{r['snippet']}")

    has_web_content = len(parts) > 0
    context_block = "\n\n---\n\n".join(parts[:7]) if parts else ""

    if has_web_content:
        log.info(f"[Research] analyser: using {len(parts)} web sources")
        source_instruction = f"Use this web research content:\n\n{context_block}"
    else:
        log.warning("[Research] analyser: no web content — using LLM knowledge")
        source_instruction = (
            "No web content was retrieved. Use your own expert knowledge "
            "to write a comprehensive, accurate report on this topic. "
            "Be specific with real facts, tools, frameworks, and numbers you know."
        )

    prompt = f"""You are a senior research analyst. Write a professional research report.

TOPIC: "{topic}"

{source_instruction}

Write a structured report with these exact sections:
## Executive Summary
(3-4 sentences on what this is and why it matters now)

## Key Findings
(6-8 specific, concrete findings — use real names, numbers, percentages)

## Detailed Analysis
(2-3 paragraphs of deep analysis — patterns, comparisons, implications)

## Current Trends & Developments
(What is happening right now — specific tools, frameworks, companies)

## Key Players / Technologies / Frameworks
(Concrete names: actual tools, companies, people — no vague lists)

## Recommendations
(4-5 actionable recommendations with specific next steps)

Rules:
- Be specific — name real tools, companies, frameworks
- No filler phrases like "it is important to note"
- 600-800 words total
- Write as if you are a paid industry analyst"""

    try:
        resp     = _llm().invoke(prompt)
        analysis = resp.content
        log.info(f"[Research] analyser: {len(analysis)} chars — {'web+LLM' if has_web_content else 'LLM knowledge'}")
        return {"analysis": analysis}
    except Exception as e:
        log.error(f"[Research] analyser LLM failed: {e}")
        return {"analysis": f"Analysis failed: {e}"}


# -----------------------------------------------------------------
# NODE 5 — Memory Writer
# Persists findings to ChromaDB for reuse by Web Builder (Phase 3)
# -----------------------------------------------------------------
def memory_writer(state: MasterState) -> dict[str, Any]:
    log = get_logger(__name__)
    log.info("[Research] memory_writer started")

    topic    = state.get("current_topic", "unknown")
    analysis = state.get("analysis", "")
    step     = _current_step(state)
    step_num = step["step"] if step else 0

    memory_key = _make_memory_key(topic, step_num)

    try:
        import chromadb
        client     = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_or_create_collection(
            name="research_memory",
            metadata={"hnsw:space": "cosine"},
        )

        collection.upsert(
            ids=[memory_key],
            documents=[analysis],
            metadatas=[{
                "topic":    topic,
                "step":     step_num,
                "length":   len(analysis),
            }],
        )
        log.info(f"[Research] memory_writer: saved '{memory_key}' to ChromaDB")

        existing_keys = state.get("memory_keys", [])
        return {"memory_keys": existing_keys + [memory_key]}

    except Exception as e:
        log.error(f"[Research] memory_writer failed: {e}")
        return {"memory_keys": state.get("memory_keys", [])}


# -----------------------------------------------------------------
# NODE 6 — Reviewer
# Quality checks the analysis. Routes back to searcher if gaps.
# Sets __route__ key for conditional edge routing.
# -----------------------------------------------------------------
def reviewer(state: MasterState) -> dict[str, Any]:
    log = get_logger(__name__)
    log.info("[Research] reviewer started")

    topic     = state.get("current_topic", "")
    analysis  = state.get("analysis", "")
    iteration = state.get("review_iteration", 0)
    max_loops = _settings().max_review_loops

    # Hard cap
    if iteration >= max_loops:
        log.info(f"[Research] reviewer: max loops reached — approving")
        return {"review_route": "reporter"}

    # Fast approve if analysis is substantial and structured
    if len(analysis) > 500 and "##" in analysis:
        log.info(f"[Research] reviewer: APPROVED ({len(analysis)} chars, structured)")
        return {"review_route": "reporter"}

    # LLM quality check
    try:
        prompt = f"""You are a quality reviewer. Evaluate this research analysis.

Topic: "{topic}"
Analysis ({len(analysis)} chars):
{analysis[:2000]}

Does this analysis:
1. Cover the topic with real, specific information?
2. Have structured sections?
3. Contain at least 3 concrete facts/examples?

If ALL yes → approved. If ANY no → list specific gaps.

Return ONLY JSON: {{"approved": true/false, "gaps": []}}"""

        resp = _llm().invoke(prompt)
        data = safe_json(resp.content, default={"approved": True, "gaps": []})

        if data.get("approved", True) or not data.get("gaps", []):
            log.info("[Research] reviewer: LLM APPROVED")
            return {"review_route": "reporter"}
        else:
            gaps = data.get("gaps", [])
            log.info(f"[Research] reviewer: gaps found — loop {iteration+1}: {gaps}")
            gap_queries = [f"{topic} {g[:40]}" for g in gaps[:2]]
            return {
                "review_iteration":       iteration + 1,
                "current_search_queries": gap_queries,
                "review_route":           "searcher",   # ← fixed key name
            }
    except Exception as e:
        log.warning(f"[Research] reviewer LLM failed: {e} — auto-approving")
        return {"review_route": "reporter"}


# -----------------------------------------------------------------
# Conditional edge router — reads __review_route__ from state
# -----------------------------------------------------------------
def route_reviewer(state: MasterState) -> str:
    """LangGraph conditional edge — reads properly typed state key."""
    route = state.get("review_route", "reporter")
    get_logger(__name__).debug(f"[Research] routing → {route}")
    return route


# -----------------------------------------------------------------
# NODE 7 — Reporter
# Packages everything into a clean ResearchReport and appends
# it to state["research_reports"]
# -----------------------------------------------------------------
def reporter(state: MasterState) -> dict[str, Any]:
    log = get_logger(__name__)
    log.info("[Research] reporter started")

    step     = _current_step(state)
    step_num = step["step"] if step else 0

    # ── Read analysis NOW before any clearing ──────────────────────
    analysis = state.get("analysis", "")
    topic    = state.get("current_topic", state.get("research_topic", "unknown"))
    results  = state.get("search_results", [])
    mem_key  = _make_memory_key(topic, step_num)

    # Guard: if still empty, write a note (shouldn't happen now)
    if not analysis or len(analysis) < 50:
        analysis = f"Research on '{topic}' could not retrieve sufficient content. Topic noted for retry."
        log.warning(f"[Research] reporter: analysis was empty — using placeholder")

    # Extract summary from first non-empty line
    lines   = [l.strip() for l in analysis.split("\n") if l.strip() and not l.startswith("#")]
    summary = lines[0][:300] if lines else analysis[:300]

    sources = list({r["url"] for r in results if _is_valid_url(r.get("url",""))})[:8]

    report = ResearchReport(
        step_id    = step_num,
        topic      = topic,
        summary    = summary,
        findings   = analysis,
        sources    = sources,
        memory_key = mem_key,
    )

    existing = state.get("research_reports", [])
    log.info(f"[Research] reporter: report #{step_num} ready — {len(analysis)} chars ✅")

    return {
        "research_reports":     existing + [report],
        # Clear working state for next step
        "current_search_queries": [],
        "search_results":         [],
        "scraped_content":        [],
        "analysis":               "",
        "review_route":           "",
    }