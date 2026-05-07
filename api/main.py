# api/main.py
from __future__ import annotations
import asyncio, json, os
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from api.schemas import AgentRequest, AgentResponse, PageResponse, ReportResponse
from config import get_settings
from graphs import get_planning_graph, get_research_graph, get_web_builder_graph
from state import AgentMode, MasterState, NextGraph
from utils import get_logger

log      = get_logger(__name__)
settings = get_settings()

app = FastAPI(
    title="Synapse AI — Research & Build Intelligence API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://synapse-ai-delta-coral.vercel.app/",   # ← your vercel URL
        "https://*.vercel.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Disk-based page store (survives restarts) ──────────────────────
PAGES_DIR = "/tmp/generated_pages"
os.makedirs(PAGES_DIR, exist_ok=True)

def _save_page(page_id: str, html: str) -> None:
    with open(f"{PAGES_DIR}/{page_id}.html", "w", encoding="utf-8") as f:
        f.write(html)

def _load_page(page_id: str) -> str | None:
    path = f"{PAGES_DIR}/{page_id}.html"
    return open(path, encoding="utf-8").read() if os.path.exists(path) else None


# ── SSE formatter ─────────────────────────────────────────────────
def _sse(event: str, graph: str, node: str, msg: str, data: dict | None = None) -> str:
    payload = json.dumps({"event": event, "graph": graph,
                          "node": node, "message": msg, "data": data or {}})
    return f"data: {payload}\n\n"


# ── Core runner (sync — called in executor thread) ────────────────
def _run_agent(req: AgentRequest, emit) -> MasterState:
    # Phase 1 — Planning
    emit("start", "planner", "task_splitter", "Planning Graph started")
    init: MasterState = {"user_query": req.query}  # type: ignore
    if req.mode != "auto":
        init["user_mode"] = AgentMode(req.mode.value)

    state: MasterState = get_planning_graph().invoke(init)  # type: ignore
    plan     = state.get("execution_plan", [])
    mode_val = state.get("mode", AgentMode.RESEARCH)

    emit("done", "planner", "plan_emitter",
         f"Plan ready — {len(plan)} steps",
         {"intent": state.get("intent_summary", ""), "mode": mode_val.value})

    max_steps  = req.max_steps
    res_steps  = [s for s in plan if s["graph"] == "research"]
    bld_steps  = [s for s in plan if s["graph"] == "builder"]
    if max_steps:
        res_steps = res_steps[:max_steps]
        bld_steps = bld_steps[:max_steps]

    # Phase 2 — Research
    if mode_val in (AgentMode.RESEARCH, AgentMode.BOTH):
        for step in res_steps:
            emit("start", "research", "sub_planner", f"Researching: {step['task'][:60]}")
            step_state: MasterState = {
                **state,  # type: ignore
                "current_research_step":  plan.index(step),
                "current_topic":          step["task"],
                "current_search_queries": step.get("search_queries", []),
                "review_iteration": 0,
                "search_results":   [],
                "scraped_content":  [],
                "analysis":         "",
                "review_route":     "",
            }
            result  = get_research_graph().invoke(step_state)  # type: ignore
            reports = result.get("research_reports", [])
            if reports:
                state = {**state,  # type: ignore
                         "research_reports": reports,
                         "memory_keys": result.get("memory_keys", [])}
                emit("done", "research", "reporter",
                     f"Report ready — {len(reports[-1].get('findings',''))} chars",
                     {"topic": reports[-1].get("topic", "")})

    # Phase 3 — Builder
    # Phase 3 — Builder  — REPLACE this whole block
    # Phase 3 — Builder
    if mode_val in (AgentMode.BUILDER, AgentMode.BOTH):
        page_ids: dict[int, str] = {}

        # ── Pull ALL research findings to inject into builder ──────
        research_text = "\n\n---\n\n".join(
            f"TOPIC: {r.get('topic', '')}\n{r.get('findings', '')[:3000]}"
            for r in state.get("research_reports", [])[:3]
        )

        for step in bld_steps:
            emit("start", "builder", "requirements_parser",
                 f"Building: {step['task'][:60]}")

            step_state: MasterState = {
                **state,  # type: ignore
                "current_builder_step": plan.index(step),
                "build_description": state.get("user_query", step["task"]),
                "build_research_ctx": research_text,  # ← KEY FIX
                "research_topic": state.get("research_topic", step["task"]),
                "fix_attempts": 0,
                "build_errors": [],
            }
            result = get_web_builder_graph().invoke(step_state)  # type: ignore
            pages = result.get("built_pages", [])
            if pages:
                page = pages[-1]
                pid = f"page_{step['step']}"  # ← always use step['step']
                page_ids[step["step"]] = pid  # ← store mapping
                _save_page(pid, page.get("html", ""))
                log.info(f"[API] Saved page to generated_pages/{pid}.html")
                state = {**state, "built_pages": pages}  # type: ignore
                emit("done", "builder", "seo_enhancer",
                     f"Page built — {len(page.get('html', ''))} chars",
                     {"page_id": pid, "css_lines": page.get("css_lines", 0)})
    return state


# ── GET /api/health ───────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Synapse AI", "version": "1.0.0"}


# ── POST /api/run (JSON) ──────────────────────────────────────────
@app.post("/api/run", response_model=AgentResponse)
async def run_agent(req: AgentRequest):
    try:
        loop   = asyncio.get_running_loop()
        events = []
        state  = await loop.run_in_executor(
            None, lambda: _run_agent(req, lambda *a, **k: events.append(a))
        )
        reports = [ReportResponse(
            step_id=r.get("step_id", 0), topic=r.get("topic", ""),
            summary=r.get("summary", ""), findings=r.get("findings", ""),
            sources=r.get("sources", []),
        ) for r in state.get("research_reports", [])]

        pages = [PageResponse(
            step_id=p.get("step_id", 0), description=p.get("description", ""),
            html=p.get("html", ""), css_lines=p.get("css_lines", 0),
            js_lines=p.get("js_lines", 0),
        ) for p in state.get("built_pages", [])]

        return AgentResponse(
            success=True,
            mode=state.get("mode", "").value if hasattr(state.get("mode", ""), "value") else "",
            intent_summary=state.get("intent_summary", ""),
            research_reports=reports,
            built_pages=pages,
            execution_steps=len(state.get("execution_plan", [])),
        )
    except Exception as e:
        log.exception("Agent run failed")
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /api/stream (SSE) ────────────────────────────────────────
@app.post("/api/stream")
async def stream_agent(req: AgentRequest):
    async def generator() -> AsyncGenerator[str, None]:
        queue: asyncio.Queue[str | None] = asyncio.Queue()
        loop = asyncio.get_running_loop()   # capture before thread starts

        def emit(event, graph, node, msg, data=None):
            payload = _sse(event, graph, node, msg, data)
            loop.call_soon_threadsafe(queue.put_nowait, payload)

        # In stream_agent, REPLACE the entire run() coroutine:
        async def run():
            try:
                captured_pids: list[str] = []  # ← capture pids

                def emit_and_track(event, graph, node, msg, data=None):
                    emit(event, graph, node, msg, data)
                    if event == "done" and graph == "builder" and data:
                        pid = data.get("page_id", "")
                        if pid:
                            captured_pids.append(pid)

                state = await loop.run_in_executor(
                    None, lambda: _run_agent(req, emit_and_track)  # ← use wrapper
                )
                reports = state.get("research_reports", [])
                pages = state.get("built_pages", [])

                final = {
                    "reports": [
                        {"topic": r.get("topic", ""),
                         "findings": r.get("findings", ""),
                         "sources": r.get("sources", [])}
                        for r in reports
                    ],
                    "pages": [
                        {"description": p.get("description", ""),
                         "page_id": captured_pids[i] if i < len(captured_pids) else f"page_{i + 1}"}
                        for i, p in enumerate(pages)
                    ],
                }
                await queue.put(_sse("result", "system", "final", "Complete", final))
            except Exception as e:
                log.exception("Stream failed")
                await queue.put(_sse("error", "system", "error", str(e)))
            finally:
                await queue.put(None)

        asyncio.ensure_future(run())
        yield ": keep-alive\n\n"
        while True:
            item = await queue.get()
            if item is None:
                break
            yield item

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── GET /api/page/{page_id} ───────────────────────────────────────
@app.get("/api/page/{page_id}", response_class=HTMLResponse)
async def get_page(page_id: str):
    html = _load_page(page_id)
    if not html:
        raise HTTPException(status_code=404, detail="Page not found")
    return HTMLResponse(content=html)