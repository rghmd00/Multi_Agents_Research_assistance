from pydantic import BaseModel, Field

from src.graph.state import AgentState, ResearchTopic, Finding
from src.llm import llm_json

CRITIC_PROMPT = """Check this research summary against its sources. Flag any
claim that is NOT supported by the source material below.

Topic: {topic}
Summary: {text}
Sources (IDs only, not full text): {sources}

Respond with ONLY a JSON object in exactly this shape, no other text:
{{"verified": true or false, "gaps": ["unsupported claim 1", "..."]}}
If every claim is supported, use "gaps": [].
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