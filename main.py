import sqlite3
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

# ── Langfuse imports ──────────────────────────────────────────────────────────
from langfuse import get_client
from langfuse.langchain import CallbackHandler

from src.graph.workflow import build_graph
from src.graph.state import initial_state

# Load environment variables (.env should have LANGFUSE_PUBLIC_KEY, etc.)
load_dotenv()

console = Console()


def cli_human_approval_handler(interrupt_payload: dict) -> dict:
    console.print(Panel(
        f"[bold]{interrupt_payload.get('research_question', '')}[/bold]",
        title="Research question",
    ))

    table = Table(title="Proposed research plan")
    table.add_column("#", justify="right")
    table.add_column("Topic")

    for i, topic in enumerate(interrupt_payload.get("plan", []), start=1):
        table.add_row(str(i), topic.get("title", ""))

    console.print(table)

    approved = Confirm.ask("Approve this plan?", default=True)
    if approved:
        return {"approved": True}

    feedback = Prompt.ask("What should change about the plan?")
    return {"approved": False, "feedback": feedback}


def render_report(report_sections: list[dict]) -> None:
    console.rule("[bold green]Final research report")
    for section in report_sections:
        console.print(Panel(
            Markdown(section["text"]),
            title=section["topic"],
            subtitle=f"Sources: {', '.join(section.get('citations', [])) or 'none'}",
        ))


def run_research_session(research_question: str, graph) -> None:
    """Runs one research session on an already-built graph with Langfuse tracing."""
    session_id = str(uuid.uuid4())

    # 1. Initialize Langfuse CallbackHandler for this session
    langfuse_handler = CallbackHandler()

    # 2. Attach handler to callbacks and pass session metadata
    config = {
        "configurable": {"thread_id": session_id},
        "recursion_limit": 60,
        "callbacks": [langfuse_handler],
        "metadata": {
            "session_id": session_id,
            "research_question": research_question,
            "agent_type": "deep_research",
        },
    }

    state = initial_state(research_question, session_id)

    # Initial invocation (runs until human_approval interrupt)
    result = graph.invoke(state, config)

    # Resume loop for human-in-the-loop approvals
    while "__interrupt__" in result:
        pending_interrupt = result["__interrupt__"][0]
        decision = cli_human_approval_handler(pending_interrupt.value)
        # Passing config ensures resumed runs attach to the same Langfuse trace
        result = graph.invoke(Command(resume=decision), config)

    report = result.get("compiled_report", [])
    if not report:
        console.print("[red]No report was generated.[/red]")
        return

    normalized = [
        section.to_dict() if hasattr(section, "to_dict") else section
        for section in report
    ]
    render_report(normalized)


def main() -> None:
    console.print(Panel("[bold cyan]Deep Research Assistant[/bold cyan]", expand=False))

    research_question = (
        " ".join(sys.argv[1:]) if len(sys.argv) > 1
        else Prompt.ask("What would you like researched?")
    )

    Path("data").mkdir(exist_ok=True)

    # ── app startup ──────────────────────────────────────────────────────
    conn = sqlite3.connect("data/checkpoints.db", check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    graph = build_graph(checkpointer)

    try:
        run_research_session(research_question, graph)
    except KeyboardInterrupt:
        console.print("\n[yellow]Session interrupted by user.[/yellow]")
    finally:
        # ── app shutdown ─────────────────────────────────────────────────
        # Flush any batched telemetry events to Langfuse before exit
        try:
            get_client().flush()
        except Exception:
            pass
        conn.close()


if __name__ == "__main__":
    main()