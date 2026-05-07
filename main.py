# main.py
# -----------------------------------------------------------------
# CLI entry point — Phase 1 + Phase 2
#
# Runs Planning Graph → then Research Graph for every research step
#
# Usage:
#   python main.py --query "Analyse AI agent frameworks 2025" --mode research
#   python main.py --query "Research EVs" --mode research --steps 2
# -----------------------------------------------------------------
from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from config import get_settings
from graphs import get_planning_graph, get_research_graph
from state import AgentMode, MasterState, NextGraph
from utils import get_logger

app     = typer.Typer(help="AI Agent System — Phase 1 + 2")
console = Console()
log     = get_logger(__name__)


# -----------------------------------------------------------------
# Display helpers
# -----------------------------------------------------------------
def _banner():
    console.print(Panel.fit(
        "[bold cyan]AI Agent System[/bold cyan] · "
        "[dim]Phase 2 — Planning + Research[/dim]\n"
        "[dim]LangGraph · Groq · Tavily · ChromaDB · All Free[/dim]",
        border_style="cyan",
    ))


def _print_plan(state: MasterState):
    console.print(Panel(
        f"[bold]{state.get('intent_summary', '')}[/bold]\n"
        f"[dim]Mode: [cyan]{state.get('mode','').value}[/cyan]  "
        f"| Topic: [green]{state.get('research_topic','N/A')}[/green][/dim]",
        title="[bold yellow]Manager Decision[/bold yellow]",
        border_style="yellow",
    ))

    plan = state.get("execution_plan", [])
    tbl  = Table(show_header=True, header_style="bold cyan",
                 border_style="dim", show_lines=True)
    tbl.add_column("#",    width=4,  style="dim")
    tbl.add_column("Graph",width=12)
    tbl.add_column("Task", min_width=36)
    tbl.add_column("Deps", width=6, style="dim")

    for s in plan:
        g = "[cyan]Research[/cyan]" if s["graph"]=="research" else "[magenta]Builder[/magenta]"
        d = ", ".join(str(x) for x in s.get("depends_on",[])) or "—"
        tbl.add_row(str(s["step"]), g, s["task"][:55], d)
    console.print(tbl)


def _print_report(report: dict, index: int):
    console.print()
    console.print(Rule(f"[bold cyan]Research Report #{index + 1}[/bold cyan]"))
    console.print(f"[bold]Topic:[/bold] {report.get('topic', '')}\n")
    findings = report.get("findings", "No findings.")
    console.print(findings)
    sources = report.get("sources", [])
    if sources:
        console.print(f"\n[dim]Sources ({len(sources)}):[/dim]")
        for s in sources[:5]:
            console.print(f"  [dim]· {s}[/dim]")


# -----------------------------------------------------------------
# Main command
# -----------------------------------------------------------------
@app.command()
def run(
    query: Optional[str] = typer.Option(
        None, "--query", "-q", help="Research topic or instruction"
    ),
    mode: Optional[str] = typer.Option(
        None, "--mode", "-m", help="research | builder | both"
    ),
    steps: Optional[int] = typer.Option(
        None, "--steps", "-s",
        help="Max research steps to run (default: all)"
    ),
    dump_json: bool = typer.Option(
        False, "--json", help="Dump full state JSON"
    ),
):
    """Run Planning Graph then Research Graph for all research steps."""
    _banner()

    if not query:
        query = typer.prompt("What should the agent research?")

    # Build initial state
    init: MasterState = {"user_query": query}  # type: ignore
    if mode:
        try:
            init["user_mode"] = AgentMode(mode.lower())
            console.print(f"[dim]Mode: [yellow]{mode}[/yellow][/dim]\n")
        except ValueError:
            console.print(f"[red]Invalid mode. Use: research | builder | both[/red]")
            raise typer.Exit(1)

    # ── PHASE 1: Planning Graph ────────────────────────────────────
    console.print(f"[dim]Query:[/dim] [bold]{query}[/bold]\n")
    with console.status("[bold cyan]Phase 1: Planning Graph running...[/bold cyan]",
                        spinner="dots"):
        try:
            state: MasterState = get_planning_graph().invoke(init)  # type: ignore
        except Exception as e:
            console.print(f"[red]Planning failed: {e}[/red]")
            raise typer.Exit(1)

    _print_plan(state)

    # ── Check if research steps exist ─────────────────────────────
    plan = state.get("execution_plan", [])
    research_steps = [s for s in plan if s["graph"] == "research"]

    if not research_steps:
        console.print("[yellow]No research steps in plan.[/yellow]")
        raise typer.Exit(0)

    # Respect --steps limit
    if steps:
        research_steps = research_steps[:steps]

    console.print(f"\n[bold]Phase 2:[/bold] Running [cyan]{len(research_steps)}[/cyan] "
                  f"research step(s)...\n")

    # ── PHASE 2: Research Graph (once per step) ───────────────────
    research_graph = get_research_graph()
    all_reports    = []

    for i, step in enumerate(research_steps):
        console.print(Rule(f"[dim]Step {step['step']}/{len(research_steps)}: "
                           f"{step['task'][:60]}[/dim]"))

        # Inject current step info into state
        step_state: MasterState = {
            **state,  # type: ignore
            "current_research_step": plan.index(step),
            "review_iteration":      0,
            "current_search_queries": step.get("search_queries", []),
            "current_topic": step["task"],
            "search_results":         [],
            "scraped_content":        [],
            "analysis":               "",
            "__review_route__":       "",
        }

        with console.status(
            f"[cyan]Researching: {step['task'][:50]}...[/cyan]",
            spinner="dots"
        ):
            try:
                result = research_graph.invoke(step_state)  # type: ignore
                reports = result.get("research_reports", [])
                if reports:
                    # Get the last (newest) report from this step
                    new_report = reports[-1]
                    all_reports.append(new_report)
                    # Update shared state with memory keys
                    state = {
                        **state,  # type: ignore
                        "research_reports": all_reports,
                        "memory_keys": result.get("memory_keys", []),
                    }
            except Exception as e:
                console.print(f"[red]Step {step['step']} failed: {e}[/red]")
                log.exception(f"Research step {step['step']} failed")
                continue

    # ── Print all reports ─────────────────────────────────────────
    if all_reports:
        console.print()
        console.print(Rule("[bold green]Research Complete[/bold green]"))
        for i, report in enumerate(all_reports):
            _print_report(report, i)
    else:
        console.print("[red]No reports generated.[/red]")

    # ── Summary ───────────────────────────────────────────────────
    console.print()
    console.print(Panel(
        f"[bold green]Done![/bold green]\n"
        f"[dim]Reports generated : [cyan]{len(all_reports)}[/cyan]\n"
        f"ChromaDB keys saved: [cyan]{len(state.get('memory_keys', []))}[/cyan][/dim]",
        border_style="green",
        title="Phase 2 Summary",
    ))

    if dump_json:
        safe = {k: (v.value if hasattr(v,"value") else v)
                for k, v in state.items()}
        console.print_json(json.dumps(safe, default=str, indent=2))


if __name__ == "__main__":
    app()