# graphs/planning/nodes.py
# ─────────────────────────────────────────────────────────────────
# The Planning Graph — acts as the Manager Brain.
#
# Four nodes in sequence:
#   task_splitter      – breaks the goal into top-level tasks
#   subtask_generator  – expands each task into concrete subtasks
#   dependency_resolver– topological sort, assigns graphs
#   plan_emitter       – emits the final structured plan
#
# The emitter also sets `next_graph` so the Orchestrator knows
# which specialist graph to call first.
# ─────────────────────────────────────────────────────────────────
from __future__ import annotations

import json
from typing import Any

from langchain_groq import ChatGroq

from config import get_settings
from state import AgentMode, MasterState, NextGraph, PlanStep, SubTask
from utils import extract_json, extract_list, get_logger, safe_json

log = get_logger(__name__)
settings = get_settings()


# ── LLM singleton (shared across all nodes in this file) ──────────
def _get_llm() -> ChatGroq:
    return ChatGroq(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=settings.groq_api_key,
    )


# ─────────────────────────────────────────────────────────────────
# NODE 1 — Task Splitter
# ─────────────────────────────────────────────────────────────────
def task_splitter(state: MasterState) -> dict[str, Any]:
    """
    Analyse the user query and break it into:
      • detected mode  (research / builder / both)
      • 2-8 high-level tasks
      • intent summary
    """
    log.info("[Planner] task_splitter started")
    llm = _get_llm()

    mode_hint = ""
    if "user_mode" in state and state["user_mode"]:
        mode_hint = f'\nUser explicitly requested mode: "{state["user_mode"].value}" — honour it.'

    prompt = f"""You are a senior AI project manager. Analyse this user request and decompose it.

User request: "{state['user_query']}"{mode_hint}

Rules:
- mode must be "research", "builder", or "both"
  * "research" → user wants analysis / report on a topic
  * "builder"  → user wants a website / page built
  * "both"     → user wants research AND a website (e.g. "research X and build a page about it")
- tasks: 2 to 8 high-level tasks, ordered logically
- intent_summary: one crisp sentence describing the goal

Return ONLY valid JSON — no markdown, no commentary:
{{
  "mode": "research" | "builder" | "both",
  "intent_summary": "...",
  "research_topic": "main topic to research or null",
  "website_type": "type and purpose of website or null",
  "website_uses_research": true | false,
  "tasks": [
    "high-level task 1",
    "high-level task 2"
  ]
}}"""

    response = llm.invoke(prompt)
    data = safe_json(
        response.content,
        default={
            "mode": "research",
            "intent_summary": state["user_query"],
            "research_topic": state["user_query"],
            "website_type": None,
            "website_uses_research": False,
            "tasks": [state["user_query"]],
        },
    )

    # If user forced a mode, respect it
    if "user_mode" in state and state["user_mode"]:
        data["mode"] = state["user_mode"].value

    detected_mode = AgentMode(data.get("mode", "research"))
    raw_tasks = data.get("tasks", [state["user_query"]])

    log.info(
        f"[Planner] Mode={detected_mode.value} | Tasks={len(raw_tasks)} | "
        f"Summary={data.get('intent_summary','')}"
    )

    return {
        "mode":                   detected_mode,
        "intent_summary":         data.get("intent_summary", state["user_query"]),
        "research_topic":         data.get("research_topic"),
        "website_type":           data.get("website_type"),
        "website_uses_research":  bool(data.get("website_uses_research", False)),
        "raw_tasks":              raw_tasks,
    }


# ─────────────────────────────────────────────────────────────────
# NODE 2 — Subtask Generator
# ─────────────────────────────────────────────────────────────────
def subtask_generator(state: MasterState) -> dict[str, Any]:
    """
    Expand each high-level task into 2-4 concrete subtasks.
    Assigns tool_hint so the dependency resolver knows which
    specialist graph to route each subtask to.
    """
    log.info(f"[Planner] subtask_generator — expanding {len(state['raw_tasks'])} tasks")
    llm = _get_llm()

    tasks_json = json.dumps(state["raw_tasks"], indent=2)
    mode = state.get("mode", AgentMode.RESEARCH).value

    prompt = f"""You are a senior AI project manager. Expand these high-level tasks into subtasks.

Overall goal: "{state['user_query']}"
Mode: {mode}
High-level tasks:
{tasks_json}

For each task create 2-4 concrete subtasks.
tool_hint: "research" for tasks needing web search/analysis, "builder" for website/UI generation, "none" for planning steps.
estimated_min: realistic minutes to complete.

Return ONLY valid JSON:
{{
  "subtasks": [
    {{
      "id": "st_01",
      "parent_task": "exact task name from list",
      "description": "specific action to take",
      "tool_hint": "research" | "builder" | "none",
      "estimated_min": 5
    }}
  ]
}}"""

    response = llm.invoke(prompt)
    data = safe_json(response.content, default={"subtasks": []})

    subtasks: list[SubTask] = data.get("subtasks", [])
    log.info(f"[Planner] Generated {len(subtasks)} subtasks")

    return {"subtasks": subtasks}


# ─────────────────────────────────────────────────────────────────
# NODE 3 — Dependency Resolver
# ─────────────────────────────────────────────────────────────────
def dependency_resolver(state: MasterState) -> dict[str, Any]:
    """
    Build an ordered execution plan with dependency resolution.

    Strategy:
      1. Ask LLM to produce a dependency map + search queries
      2. Perform a topological sort (Kahn's algorithm)
      3. Return ordered PlanStep list + dependency DAG

    Research steps are always placed before builder steps when
    website_uses_research=True, so real content flows into pages.
    """
    log.info("[Planner] dependency_resolver — building execution plan")
    llm = _get_llm()

    mode = state.get("mode", AgentMode.RESEARCH).value
    tasks = state.get("raw_tasks", [])
    tasks_json = json.dumps(tasks, indent=2)

    prompt = f"""You are a senior AI engineer. Create an ordered execution plan.

Goal: "{state['user_query']}"
Mode: {mode}
Tasks: {tasks_json}
website_uses_research: {state.get("website_uses_research", False)}

Rules:
- Each step has a unique step number starting at 1
- graph: "research" or "builder" — pick based on task nature
- depends_on: list of step numbers that must complete first (use [] if none)
- If website_uses_research=true, all research steps must come before builder steps
- search_queries: 2-3 specific web search queries (for research steps, else [])
- page_sections: list of page sections (for builder steps, else [])

Return ONLY valid JSON:
{{
  "steps": [
    {{
      "step": 1,
      "graph": "research",
      "task": "task description",
      "depends_on": [],
      "search_queries": ["query 1", "query 2"],
      "page_sections": []
    }},
    {{
      "step": 2,
      "graph": "builder",
      "task": "build landing page",
      "depends_on": [1],
      "search_queries": [],
      "page_sections": ["Hero", "Features", "Pricing", "Footer"]
    }}
  ]
}}"""

    response = llm.invoke(prompt)
    data = safe_json(response.content, default={"steps": []})

    raw_steps = data.get("steps", [])

    # ── Topological sort (Kahn's algorithm) ───────────────────────
    sorted_steps = _topological_sort(raw_steps)

    # ── Build PlanStep list ───────────────────────────────────────
    plan: list[PlanStep] = []
    dag: dict[str, list[str]] = {}

    for s in sorted_steps:
        step_id = str(s.get("step", len(plan) + 1))
        deps = [str(d) for d in s.get("depends_on", [])]
        dag[step_id] = deps

        plan.append(
            PlanStep(
                step=s.get("step", len(plan) + 1),
                graph=s.get("graph", "research"),
                task=s.get("task", ""),
                subtasks=[],
                depends_on=s.get("depends_on", []),
                status="pending",
                search_queries=s.get("search_queries", []),
                page_sections=s.get("page_sections", []),
            )
        )

    log.info(f"[Planner] Execution plan: {len(plan)} steps")
    for step in plan:
        log.debug(
            f"  Step {step['step']} [{step['graph'].upper()}] "
            f"depends_on={step['depends_on']} — {step['task'][:60]}"
        )

    return {
        "execution_plan":  plan,
        "dependency_dag":  dag,
        "current_step":    0,
        "completed_steps": [],
        "failed_steps":    [],
    }


def _topological_sort(steps: list[dict]) -> list[dict]:
    """Kahn's algorithm for topological ordering."""
    if not steps:
        return steps

    step_map = {s["step"]: s for s in steps}
    in_degree: dict[int, int] = {s["step"]: 0 for s in steps}

    for s in steps:
        for dep in s.get("depends_on", []):
            if dep in in_degree:
                in_degree[s["step"]] = in_degree.get(s["step"], 0) + 1

    # Start with zero in-degree nodes
    queue = [sid for sid, deg in in_degree.items() if deg == 0]
    sorted_ids: list[int] = []

    while queue:
        node = queue.pop(0)
        sorted_ids.append(node)
        for s in steps:
            if node in s.get("depends_on", []):
                in_degree[s["step"]] -= 1
                if in_degree[s["step"]] == 0:
                    queue.append(s["step"])

    # If cycle detected, fall back to original order
    if len(sorted_ids) != len(steps):
        log.warning("[Planner] Dependency cycle detected — using original order")
        return steps

    return [step_map[sid] for sid in sorted_ids if sid in step_map]


# ─────────────────────────────────────────────────────────────────
# NODE 4 — Plan Emitter
# ─────────────────────────────────────────────────────────────────
def plan_emitter(state: MasterState) -> dict[str, Any]:
    """
    Determine which graph to invoke first and set next_graph.
    This is the Planning Graph's final output — it hands off
    control to the Orchestrator.
    """
    log.info("[Planner] plan_emitter — determining first graph to invoke")

    plan    = state.get("execution_plan", [])
    current = state.get("current_step", 0)

    if not plan or current >= len(plan):
        log.info("[Planner] No steps or all steps complete → DONE")
        return {"next_graph": NextGraph.DONE}

    next_step = plan[current]
    graph_key = next_step.get("graph", "research")

    next_graph = NextGraph.RESEARCH if graph_key == "research" else NextGraph.BUILDER

    log.info(
        f"[Planner] Next: Step {next_step['step']} "
        f"[{graph_key.upper()}] — {next_step['task'][:60]}"
    )

    return {"next_graph": next_graph}