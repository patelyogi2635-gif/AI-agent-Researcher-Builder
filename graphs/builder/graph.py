# graphs/builder/graph.py
from __future__ import annotations
from functools import lru_cache
from langgraph.graph import END, START, StateGraph
from state import MasterState
from utils import get_logger
from .nodes import (
    requirements_parser, wireframe_planner, html_generator,
    css_styler, js_generator, validator, route_validator,
    self_healer, seo_enhancer,
)

log = get_logger(__name__)

def build_web_builder_graph():
    b = StateGraph(MasterState)
    b.add_node("requirements_parser", requirements_parser)
    b.add_node("wireframe_planner",   wireframe_planner)
    b.add_node("html_generator",      html_generator)
    b.add_node("css_styler",          css_styler)
    b.add_node("js_generator",        js_generator)
    b.add_node("validator",           validator)
    b.add_node("self_healer",         self_healer)
    b.add_node("seo_enhancer",        seo_enhancer)

    b.add_edge(START,                  "requirements_parser")
    b.add_edge("requirements_parser",  "wireframe_planner")
    b.add_edge("wireframe_planner",    "html_generator")
    b.add_edge("html_generator",       "css_styler")
    b.add_edge("css_styler",           "js_generator")
    b.add_edge("js_generator",         "validator")
    b.add_conditional_edges("validator", route_validator,
        {"self_healer": "self_healer", "seo_enhancer": "seo_enhancer"})
    b.add_edge("self_healer",          "seo_enhancer")
    b.add_edge("seo_enhancer",         END)
    log.debug("[BuilderGraph] Compiled")
    return b.compile()

@lru_cache(maxsize=1)
def get_web_builder_graph():
    return build_web_builder_graph()