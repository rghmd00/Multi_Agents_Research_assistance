from dataclasses import dataclass, field, asdict
from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages


# ─────────────────────────────────────────────────────────────────────────────
# Nested data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ResearchTopic:
    """One sub-topic in the research plan, created by research_planner_node."""
    title: str
    status: Literal["pending", "researching", "verified", "written"] = "pending"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchTopic":
        return cls(
            title=data["title"],
            status=data.get("status", "pending"),
        )


@dataclass
class Finding:
    """Raw research output for one topic, written by researcher_node."""
    sources: list[str] = field(default_factory=list)      # arxiv IDs / URLs
    extracted_text: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Finding":
        return cls(
            sources=list(data.get("sources", [])),
            extracted_text=data.get("extracted_text", ""),
        )


@dataclass
class ReportSection:
    """One finished, cited section, written by report_writer_node."""
    topic: str
    text: str
    citations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ReportSection":
        return cls(
            topic=data["topic"],
            text=data.get("text", ""),
            citations=list(data.get("citations", [])),
        )


# ─────────────────────────────────────────────────────────────────────────────
# AgentState
# ─────────────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    session_id: str
    research_question: str

    # Planning + human approval
    plan: list[ResearchTopic]
    approved: bool
    rejection_feedback: str | None
    plan_attempts: int                 # bounds the rejection loop

    # Research loop (per current topic)
    current_topic_index: int
    research_attempts: int             # bounds the research loop for THIS topic
    raw_findings: dict[str, Finding]   # keyed by topic title
    gaps: list[str]
    verified: bool

    # Output
    compiled_report: list[ReportSection]

    # Conversation / tool-call history, merged automatically each node
    messages: Annotated[list, add_messages]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def initial_state(research_question: str, session_id: str) -> AgentState:
    return AgentState(
        session_id=session_id,
        research_question=research_question,
        plan=[],
        approved=False,
        rejection_feedback=None,
        plan_attempts=0,
        current_topic_index=0,
        research_attempts=0,
        raw_findings={},
        gaps=[],
        verified=False,
        compiled_report=[],
        messages=[],
    )


def is_session_finished(state: AgentState) -> bool:
    """True once every topic in the plan has a written report section."""
    return state["current_topic_index"] >= len(state["plan"])