# graphs/research/graph.py
# -----------------------------------------------------------------
# Compiles the Research Graph with a conditional reviewer loop.
#
# Flow:
#   START
#     → sub_planner
#     → searcher
#     → scraper
#     → analyser
#     → memory_writer
#     → reviewer  ──(gaps found)──→ searcher  (loop, max 3x)
#         └──(approved)──→ reporter
#   END
# -----------------------------------------------------------------
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from state import MasterState
from utils import get_logger

from .nodes import (
    analyser,
    memory_writer,
    reporter,
    reviewer,
    route_reviewer,
    scraper,
    searcher,
    sub_planner,
)

log = get_logger(__name__)

# Node name constants
_N_SUB_PLANNER    = "sub_planner"
_N_SEARCHER       = "searcher"
_N_SCRAPER        = "scraper"
_N_ANALYSER       = "analyser"
_N_MEMORY_WRITER  = "memory_writer"
_N_REVIEWER       = "reviewer"
_N_REPORTER       = "reporter"


def build_research_graph():
    """Build and return the compiled Research Graph."""
    builder = StateGraph(MasterState)

    # Register nodes
    builder.add_node(_N_SUB_PLANNER,   sub_planner)
    builder.add_node(_N_SEARCHER,      searcher)
    builder.add_node(_N_SCRAPER,       scraper)
    builder.add_node(_N_ANALYSER,      analyser)
    builder.add_node(_N_MEMORY_WRITER, memory_writer)
    builder.add_node(_N_REVIEWER,      reviewer)
    builder.add_node(_N_REPORTER,      reporter)

    # Linear edges
    builder.add_edge(START,            _N_SUB_PLANNER)
    builder.add_edge(_N_SUB_PLANNER,   _N_SEARCHER)
    builder.add_edge(_N_SEARCHER,      _N_SCRAPER)
    builder.add_edge(_N_SCRAPER,       _N_ANALYSER)
    builder.add_edge(_N_ANALYSER,      _N_MEMORY_WRITER)
    builder.add_edge(_N_MEMORY_WRITER, _N_REVIEWER)

    # Conditional edge — reviewer routes to searcher (loop) or reporter
    builder.add_conditional_edges(
        _N_REVIEWER,
        route_reviewer,
        {
            "searcher": _N_SEARCHER,   # loop back with gap-filling queries
            "reporter": _N_REPORTER,   # approved — write final report
        },
    )

    builder.add_edge(_N_REPORTER, END)

    log.debug("[ResearchGraph] Compiled successfully")
    return builder.compile()


@lru_cache(maxsize=1)
def get_research_graph():
    """Return cached compiled research graph (singleton)."""
    return build_research_graph()