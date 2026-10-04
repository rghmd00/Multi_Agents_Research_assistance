from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command

from src.graph.state import AgentState, is_session_finished
from src.agents.research_planner import research_planner_node
from src.agents.researcher import researcher_node
from src.agents.critic import critic_node
from src.agents.report_writer import report_writer_node

MAX_PLAN_ATTEMPTS = 2
MAX_RESEARCH_ATTEMPTS = 2


def human_approval_node(state: AgentState) -> dict:
    decision = interrupt({
        "research_question": state["research_question"],
        "plan": [t.to_dict() if hasattr(t, "to_dict") else t for t in state["plan"]],
        "prompt": "Review and approve this research plan:",
    })
    if isinstance(decision, bool):
        return {"approved": decision, "rejection_feedback": None}
    if isinstance(decision, dict):
        return {
            "approved": bool(decision.get("approved", False)),
            "rejection_feedback": decision.get("feedback"),
        }
    return {"approved": False, "rejection_feedback": str(decision)}


def route_after_approval(state: AgentState) -> str:
    if state.get("approved") and len(state.get("plan", [])) > 0:
        return "researcher"
    if state["plan_attempts"] >= MAX_PLAN_ATTEMPTS:
        return "researcher"
    return "research_planner"


def route_after_critic(state: AgentState) -> str:
    if state["verified"] or state["research_attempts"] >= MAX_RESEARCH_ATTEMPTS:
        return "report_writer"
    return "researcher"


def route_after_report(state: AgentState) -> str:
    return END if is_session_finished(state) else "researcher"


def build_graph(checkpointer):
    """Compiles the graph with an already-open checkpointer. Caller owns the
    connection's lifetime (open before, close after)."""
    builder = StateGraph(AgentState)

    builder.add_node("research_planner", research_planner_node)
    builder.add_node("human_approval", human_approval_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("critic", critic_node)
    builder.add_node("report_writer", report_writer_node)

    builder.add_edge(START, "research_planner")
    builder.add_edge("research_planner", "human_approval")
    builder.add_edge("researcher", "critic")

    builder.add_conditional_edges(
        "human_approval", route_after_approval,
        {"researcher": "researcher", "research_planner": "research_planner"},
    )
    builder.add_conditional_edges(
        "critic", route_after_critic,
        {"researcher": "researcher", "report_writer": "report_writer"},
    )
    builder.add_conditional_edges(
        "report_writer", route_after_report,
        {"researcher": "researcher", END: END},
    )

    return builder.compile(checkpointer=checkpointer)