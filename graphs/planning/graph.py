# graphs/planning/graph.py
# ─────────────────────────────────────────────────────────────────
# Compiles the Planning Graph.
#
# Flow:
#   START
#     → task_splitter
#     → subtask_generator
#     → dependency_resolver
#     → plan_emitter
#   END
#
# The emitter populates state["next_graph"] which the Orchestrator
# reads to decide which specialist graph runs next.
# ─────────────────────────────────────────────────────────────────
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from state import MasterState
from utils import get_logger

from .nodes import (
    dependency_resolver,
    plan_emitter,
    subtask_generator,
    task_splitter,
)

log = get_logger(__name__)

_NODE_TASK_SPLITTER      = "task_splitter"
_NODE_SUBTASK_GENERATOR  = "subtask_generator"
_NODE_DEPENDENCY_RESOLVER= "dependency_resolver"
_NODE_PLAN_EMITTER       = "plan_emitter"


def build_planning_graph() -> StateGraph:
    """
    Build and return the compiled Planning Graph.

    Returns a LangGraph CompiledGraph ready to call with
    `.invoke(state)` or `.stream(state)`.
    """
    builder = StateGraph(MasterState)

    # ── Register nodes ────────────────────────────────────────────
    builder.add_node(_NODE_TASK_SPLITTER,       task_splitter)
    builder.add_node(_NODE_SUBTASK_GENERATOR,   subtask_generator)
    builder.add_node(_NODE_DEPENDENCY_RESOLVER, dependency_resolver)
    builder.add_node(_NODE_PLAN_EMITTER,        plan_emitter)

    # ── Edges (linear — no conditional routing in Phase 1) ────────
    builder.add_edge(START,                       _NODE_TASK_SPLITTER)
    builder.add_edge(_NODE_TASK_SPLITTER,         _NODE_SUBTASK_GENERATOR)
    builder.add_edge(_NODE_SUBTASK_GENERATOR,     _NODE_DEPENDENCY_RESOLVER)
    builder.add_edge(_NODE_DEPENDENCY_RESOLVER,   _NODE_PLAN_EMITTER)
    builder.add_edge(_NODE_PLAN_EMITTER,          END)

    log.debug("[PlanningGraph] Graph compiled successfully")
    return builder.compile()


@lru_cache(maxsize=1)
def get_planning_graph():
    """Return cached compiled planning graph (singleton)."""
    return build_planning_graph()