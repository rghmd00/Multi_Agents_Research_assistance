from pydantic import BaseModel, Field

from src.graph.state import AgentState, ResearchTopic, Finding
from src.llm import llm_json



CRITIC_PROMPT = """Check this research summary against its sources. The summary
may contain claims that are NOT present in the sources at all — these are
fabrications, even if they don't directly contradict anything, and must be
flagged just as strictly as outright contradictions.

Topic: {topic}
Summary: {text}
Sources (IDs only, not full text): {sources}

Respond with ONLY a JSON object in exactly this shape, no other text:
{{"verified": true or false, "gaps": ["unsupported claim 1", "..."]}}

IMPORTANT: if "gaps" contains anything, "verified" MUST be false. If every
single claim traces directly back to the sources, use "gaps": [] and
"verified": true. Any claim not explicitly present in the sources — including
names, dates, places, or attributions not mentioned in the source material —
counts as unsupported.
"""


class CriticResult(BaseModel):
    verified: bool = Field(description="True only if every claim is supported")
    gaps: list[str] = Field(description="Unsupported or missing claims, empty if verified")


def critic_node(state: AgentState) -> dict:
    idx = state["current_topic_index"]

    raw_topic = state["plan"][idx]
    topic = ResearchTopic.from_dict(raw_topic) if isinstance(raw_topic, dict) else raw_topic

    raw_finding = state["raw_findings"][topic.title]
    finding = Finding.from_dict(raw_finding) if isinstance(raw_finding, dict) else raw_finding

    if not finding.sources:
        return {"verified": False, "gaps": ["No sources were retrieved; synthesis may be hallucinated."]}

    model = llm_json().with_structured_output(CriticResult, method="json_mode")

    try:
        result: CriticResult = model.invoke( #type: ignore
            CRITIC_PROMPT.format(topic=topic.title, text=finding.extracted_text, sources=finding.sources)
        )
        return {"verified": result.verified, "gaps": result.gaps}
    except Exception as e:
        return {"verified": False, "gaps": [f"Critic failed to produce a valid judgment: {e}"]}