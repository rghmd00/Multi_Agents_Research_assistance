# from src.graph.state import AgentState, ReportSection, ResearchTopic, Finding
# from src.llm import llm

# WRITER_PROMPT = """Write a clear report section on: {topic}

# Source material (this is ALL the information you have — do not add anything not in here):
# {text}

# Cite sources inline using ONLY these exact IDs: {sources}

# Rules:
# - Do NOT invent author names, publication years, or journal/venue names — none were provided, so omit them entirely.
# - Do NOT use template placeholders like [Authors] or [Journal/Conference].
# - If you don't have enough information about a paper beyond its title and abstract, just cite the ID, don't fabricate metadata.
# - 3-4 focused paragraphs, not exhaustive.
# """


# def report_writer_node(state: AgentState) -> dict:
#     idx = state["current_topic_index"]

#     raw_topic = state["plan"][idx]
#     topic = ResearchTopic.from_dict(raw_topic) if isinstance(raw_topic, dict) else raw_topic

#     raw_finding = state["raw_findings"][topic.title]
#     finding = Finding.from_dict(raw_finding) if isinstance(raw_finding, dict) else raw_finding

#     response = llm().invoke(
#         WRITER_PROMPT.format(topic=topic.title, text=finding.extracted_text, sources=finding.sources)
#     )

#     section = ReportSection(
#         topic=topic.title,
#         text=response.content, #type: ignore
#         citations=finding.sources,
#     ).to_dict()

#     return {
#         "compiled_report": state["compiled_report"] + [section],
#         "current_topic_index": idx + 1,
#         "research_attempts": 0,
#         "verified": False,
#         "gaps": [],
#     }

from src.graph.state import AgentState, ReportSection, ResearchTopic, Finding


def report_writer_node(state: AgentState) -> dict:
    idx = state["current_topic_index"]

    raw_topic = state["plan"][idx]
    topic = ResearchTopic.from_dict(raw_topic) if isinstance(raw_topic, dict) else raw_topic

    raw_finding = state["raw_findings"][topic.title]
    finding = Finding.from_dict(raw_finding) if isinstance(raw_finding, dict) else raw_finding

    section = ReportSection(
        topic=topic.title,
        text=finding.extracted_text,
        citations=finding.sources,
    ).to_dict()

    return {
        "compiled_report": state["compiled_report"] + [section],
        "current_topic_index": idx + 1,
        "research_attempts": 0,
        "verified": False,
        "gaps": [],
    }