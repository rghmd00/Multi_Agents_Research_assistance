from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field

from src.graph.state import AgentState, ResearchTopic
from src.llm import llm_json


class PlanTopic(BaseModel):
    title: str = Field(description="Short name for the sub-topic")


class ResearchPlan(BaseModel):
    topics: list[PlanTopic]


PLANNER_PROMPT = """You are a research planner. Break the research question into
3-5 focused sub-topics that are specific, genuinely distinct, and researchable.

Requirements:
- Each topic must be a concrete research question or angle, not a vague category.
- Topics must be non-overlapping and not near-duplicates.
- Prefer narrow, answerable subtopics over broad themes.
- Avoid generic umbrella labels like "applications" or "methods" unless combined with a concrete dimension.

Research question: {question}
{feedback_block}

Respond with ONLY a JSON object in exactly this shape, no other text:
{{"topics": [{{"title": "..."}}, ...]}}
"""


def research_planner_node(state: AgentState) -> dict:
    model = llm_json().with_structured_output(ResearchPlan, method="json_mode")

    feedback_block = ""
    is_revision = state.get("rejection_feedback") is not None
    if is_revision:
        feedback_block = f"\nThe previous plan was rejected. Feedback: {state['rejection_feedback']}\nRevise the plan accordingly."

    prompt = PLANNER_PROMPT.format(question=state["research_question"], feedback_block=feedback_block)

    result: ResearchPlan = model.invoke(prompt) #type: ignore
    plan = [ResearchTopic(title=t.title).to_dict() for t in result.topics]

    return {
        "plan": plan,
        "plan_attempts": state["plan_attempts"] + (1 if is_revision else 0),
        "messages": [AIMessage(content=f"Drafted plan with {len(plan)} topics.")],
    }