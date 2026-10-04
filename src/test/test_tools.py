# import os

# from langchain_ollama import ChatOllama
# from src.tools.research_tools import search_arxiv_papers

# MODEL_NAME_INSTRUCT = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")
# OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# def llm_instruct() -> ChatOllama:
#     """For nodes doing tool calling or writing prose (researcher, report_writer)."""
#     return ChatOllama(
#         model=MODEL_NAME_INSTRUCT,
#         base_url=OLLAMA_BASE_URL,
#         temperature=0.1,
#     )

# model = llm_instruct().bind_tools([search_arxiv_papers])
# response = model.invoke("Search arxiv for papers on transformer attention mechanisms.")
# print(response.tool_calls)  

from dotenv import load_dotenv
from langfuse import get_client

# 1. Load credentials from .env
load_dotenv()

# 2. Initialize the client
langfuse = get_client()

# 3. Test API connectivity and authentication
print("[1/3] Checking Langfuse API connection...")
if langfuse.auth_check():
    print(" Authentication successful! SDK communicates properly with the API.")
else:
    print(" Authentication failed. Check your keys or host URL.")
    exit(1)

# 4. Test sending a basic trace and observation
print("[2/3] Emitting a standalone test observation...")
with langfuse.start_as_current_observation(
    name="sdk_unit_test",
    as_type="span",
) as span:
    span.update(
        input={"test_query": "deep learning"},
        output={"status": "received", "sample_metric": 0.98},
        metadata={"environment": "local_dev", "tester": "user"}
    )

# 5. Flush event buffer to force immediate delivery
print("[3/3] Flushing telemetry buffer...")
langfuse.flush()
print(" Trace flushed successfully. Open your dashboard to view it!")