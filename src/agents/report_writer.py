
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