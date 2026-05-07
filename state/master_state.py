# state/master_state.py
# ─────────────────────────────────────────────────────────────────
# Single shared TypedDict that flows through ALL graphs.
# Each graph reads what it needs and writes into its own keys.
# The Orchestrator (Phase 3) manages the top-level routing.
# ─────────────────────────────────────────────────────────────────
from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional
from typing_extensions import TypedDict


# ── Enums ─────────────────────────────────────────────────────────

class AgentMode(str, Enum):
    """What the user wants the agent system to do."""
    RESEARCH = "research"
    BUILDER  = "builder"
    BOTH     = "both"


class NextGraph(str, Enum):
    """Which graph the Orchestrator should invoke next."""
    RESEARCH = "research"
    BUILDER  = "builder"
    DONE     = "done"


# ── Sub-models (plain dicts for TypedDict compatibility) ──────────

class SubTask(TypedDict):
    id:          str
    parent_task: str
    description: str
    tool_hint:   Literal["research", "builder", "none"]
    estimated_min: int


class PlanStep(TypedDict):
    step:        int
    graph:       Literal["research", "builder"]
    task:        str
    subtasks:    list[SubTask]
    depends_on:  list[int]   # step numbers this must wait for
    status:      Literal["pending", "running", "done", "failed"]
    search_queries: list[str]   # populated by planning graph
    page_sections: list[str]    # populated by planning graph (builder steps)


class ResearchReport(TypedDict):
    step_id:     int
    topic:       str
    summary:     str
    findings:    str         # full markdown
    sources:     list[str]
    memory_key:  str         # ChromaDB document ID


class BuiltPage(TypedDict):
    step_id:     int
    description: str
    html:        str
    css_lines:   int
    js_lines:    int


# ── Master State ──────────────────────────────────────────────────

class MasterState(TypedDict, total=False):
    # ── Input ──────────────────────────────────────────────────────
    user_query:             str
    user_mode:              AgentMode

    # ── Planning Graph ─────────────────────────────────────────────
    mode:                   AgentMode
    intent_summary:         str
    raw_tasks:              list[str]
    subtasks:               list[SubTask]
    dependency_dag:         dict[str, list[str]]
    execution_plan:         list[PlanStep]
    current_step:           int
    completed_steps:        list[int]
    failed_steps:           list[int]
    next_graph:             NextGraph
    research_topic:         Optional[str]
    website_type:           Optional[str]
    website_uses_research:  bool

    # ── Research Graph working state ───────────────────────────────
    current_research_step:  int
    current_topic:          str
    current_search_queries: list[str]
    search_results:         list[dict]
    scraped_content:        list[dict]
    analysis:               str
    review_iteration:       int
    review_route:           str        # ← THE FIX: was __review_route__

    # ── Research Graph outputs ─────────────────────────────────────
    research_reports:       list[ResearchReport]
    memory_keys:            list[str]

    # ── Web Builder Graph outputs ──────────────────────────────────
    built_pages:            list[BuiltPage]

    # ── Final ──────────────────────────────────────────────────────
    final_output:           dict[str, Any]
    error:                  Optional[str]