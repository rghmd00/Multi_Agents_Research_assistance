import arxiv
from ddgs import DDGS
from langchain_core.tools import tool

_arxiv_client = arxiv.Client(
    page_size=5,
    delay_seconds=1.5,
    num_retries=1,
)

_search_cache: dict[str, list[dict]] = {}


@tool
def search_arxiv_papers(query: str, max_results: int = 2) -> list[dict]:
    """Search arxiv for papers matching a query. Returns id, title, abstract,
    published date, and url for each result, sorted by relevance."""
    cache_key = f"{query}:{max_results}"
    if cache_key in _search_cache:
        return _search_cache[cache_key]

    try:
        search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
        results = [
            {
                "id": r.get_short_id(),
                "title": r.title,
                "abstract": r.summary,
                "published": r.published.strftime("%Y-%m-%d"),
                "url": r.entry_id,
            }
            for r in _arxiv_client.results(search)
        ]
        _search_cache[cache_key] = results
        return results
    except Exception as e:
        return [{"error": f"arxiv search temporarily unavailable: {e}"}]


@tool
def fetch_arxiv_paper(paper_id: str) -> dict:
    """Fetch full metadata and abstract for a specific arxiv paper by its ID."""
    try:
        search = arxiv.Search(id_list=[paper_id])
        result = next(_arxiv_client.results(search), None)
        if result is None:
            return {"error": f"No paper found for id {paper_id}"}
        return {
            "id": result.get_short_id(),
            "title": result.title,
            "abstract": result.summary,
            "authors": [a.name for a in result.authors],
            "published": result.published.strftime("%Y-%m-%d"),
            "pdf_url": result.pdf_url,
        }
    except Exception as e:
        return {"error": f"arxiv fetch temporarily unavailable: {e}"}


@tool
def web_search(query: str, max_results: int = 2) -> list[dict]:
    """Search the web for a query. Returns title, snippet, and url for each result."""
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
        return [{"title": r["title"], "snippet": r["body"], "url": r["href"]} for r in results]
    except Exception as e:
        return [{"error": f"web search temporarily unavailable: {e}"}]