import os

from langchain_ollama import ChatOllama

MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def llm_json() -> ChatOllama:
    """For nodes using with_structured_output (planner, critic) — forces valid JSON."""
    return ChatOllama(
        model=MODEL_NAME,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1,
        format="json",
    )


def llm() -> ChatOllama:
    """For nodes doing tool calling or writing prose (researcher, report_writer)."""
    return ChatOllama(
        model=MODEL_NAME,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1,
    )