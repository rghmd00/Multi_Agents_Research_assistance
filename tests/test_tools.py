import os

from langchain_ollama import ChatOllama
from src.tools.research_tools import search_arxiv_papers

MODEL_NAME_INSTRUCT = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def llm_instruct() -> ChatOllama:
    """For nodes doing tool calling or writing prose (researcher, report_writer)."""
    return ChatOllama(
        model=MODEL_NAME_INSTRUCT,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1,
    )

model = llm_instruct().bind_tools([search_arxiv_papers])
response = model.invoke("Search arxiv for papers on transformer attention mechanisms.")
print(response.tool_calls)  
