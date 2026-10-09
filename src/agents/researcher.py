
from langchain_core.messages import AIMessage, ToolMessage, BaseMessage

from src.graph.state import AgentState, Finding, ResearchTopic
from src.llm import llm
from src.tools.research_tools import search_arxiv_papers, fetch_arxiv_paper, web_search

TOOLS = [search_arxiv_papers, fetch_arxiv_paper, web_search]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}

MAX_TOOL_CALLS = 3  # was 2 — see note below


RESEARCHER_PROMPT = """Research: {topic}
{gap_block}

Call search_arxiv_papers first — required, not optional. Base every claim on
tool results only; no memory, no invented citations. If searches turn up
nothing, say that plainly.

Once you have enough, reply with a plain-text synthesis (no more tool calls).
Keep it concise — 1-2 paragraphs.
"""


def _summarize_tool_result(name: str, result) -> str:
    """Trim tool output before it re-enters context, and handle error dicts
    gracefully instead of assuming a clean success shape."""
    if name == "search_arxiv_papers":
        return "\n".join(
            f"{r['id']}: {r['title']}" if "id" in r else f"[search error: {r.get('error', 'unknown')}]"
            for r in result
        )
    if name == "fetch_arxiv_paper":
        if "error" in result:
            return f"[fetch error: {result['error']}]"
        return f"{result.get('id', '')}: {result.get('title', '')}\n{result.get('abstract', '')[:500]}"
    if name == "web_search":
        return "\n".join(
            f"{r['title']} ({r['url']})" if "url" in r else f"[search error: {r.get('error', 'unknown')}]"
            for r in result
        )
    return str(result)[:1000]


def researcher_node(state: AgentState) -> dict:
    idx = state["current_topic_index"]
    raw_topic = state["plan"][idx]
    topic = ResearchTopic.from_dict(raw_topic) if isinstance(raw_topic, dict) else raw_topic

    model = llm().bind_tools(TOOLS)

    gap_block = ""
    is_retry = state["research_attempts"] > 0
    if is_retry and state.get("gaps"):
        gap_block = f"\nA prior review found these gaps, address them: {state['gaps']}"

    messages: list[dict | BaseMessage] = [{
        "role": "user",
        "content": RESEARCHER_PROMPT.format(topic=topic.title, gap_block=gap_block),
    }]

    sources: list[str] = []
    extracted_text = ""
    made_a_tool_call = False

    for i in range(MAX_TOOL_CALLS):
        response: AIMessage = model.invoke(messages)

        if not response.tool_calls:
            if not made_a_tool_call and i == 0:
                # Model answered from memory instead of searching — discard
                # this fabricated response rather than leaving it in context,
                # where it would get resent (and potentially trusted) on
                # every subsequent call in the loop.
                messages.append({
                    "role": "user",
                    "content": "You must call search_arxiv_papers before answering. Do not answer from memory.",
                })
                continue
            extracted_text = response.content
            messages.append(response)
            break

        messages.append(response)
        made_a_tool_call = True
        for call in response.tool_calls:
            tool_result = TOOLS_BY_NAME[call["name"]].invoke(call["args"])

            if call["name"] == "search_arxiv_papers":
                sources.extend(r["id"] for r in tool_result if "id" in r)
            elif call["name"] == "fetch_arxiv_paper":
                if "error" not in tool_result:
                    sources.append(call["args"].get("paper_id", ""))
            elif call["name"] == "web_search":
                sources.extend(r["url"] for r in tool_result if "url" in r)

            messages.append(ToolMessage(
                content=_summarize_tool_result(call["name"], tool_result),
                tool_call_id=call["id"],
            ))
    else:
        final = model.invoke(messages + [{"role": "user", "content": "Summarize your findings now, no more tool calls."}])
        extracted_text = final.content

    finding = Finding(
        sources=[s for s in dict.fromkeys(sources) if s],
        extracted_text=extracted_text,  # type: ignore
    )

    return {
        "raw_findings": {**state["raw_findings"], topic.title: finding.to_dict()},
        "research_attempts": state["research_attempts"] + 1,
        "messages": [AIMessage(content=f"Gathered {len(finding.sources)} sources for {topic.title}.")],
    }
