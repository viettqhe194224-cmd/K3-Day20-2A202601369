"""Search client abstraction for ResearcherAgent."""

import json
import re
from html import unescape
from urllib.request import Request, urlopen

from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.schemas import SourceDocument

_BOILERPLATE_LINES = {
    "sign up",
    "sign in",
    "listen",
    "share",
    "unknown user",
    "open in app",
    "follow",
    "more",
}


def clean_search_snippet(value: str, title: str = "") -> str:
    """Remove common page chrome and decode HTML entities from search snippets."""

    decoded = unescape(value).replace("\u00a0", " ")
    title_key = re.sub(r"\W+", " ", title).strip().casefold()
    kept: list[str] = []
    for raw_line in decoded.splitlines():
        line = re.sub(r"^#{1,6}\s*", "", raw_line).strip()
        line = re.sub(r"^\\?[-—–]+$", "", line).strip()
        normalized = re.sub(r"\W+", " ", line).strip().casefold()
        if not line or normalized in _BOILERPLATE_LINES or normalized.isdigit():
            continue
        if title_key and normalized == title_key:
            continue
        if kept and line == kept[-1]:
            continue
        kept.append(line)
    return "\n\n".join(kept).strip()


class SearchClient:
    """Tavily search client with an explicit no-key fallback source."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        Uses Tavily when TAVILY_API_KEY is present. Without it, returns a clearly
        labelled local source so the workflow remains debuggable rather than crashing.
        """

        if not self.settings.tavily_api_key:
            return [
                SourceDocument(
                    title="Local fallback (web search not configured)",
                    snippet=f"No external evidence retrieved for: {query}",
                    metadata={"provider": "local", "reliability": "unverified"},
                )
            ]
        body = json.dumps(
            {"api_key": self.settings.tavily_api_key, "query": query, "max_results": max_results}
        ).encode("utf-8")
        request = Request(
            "https://api.tavily.com/search",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self.settings.timeout_seconds) as response:  # noqa: S310
            payload = json.load(response)
        documents: list[SourceDocument] = []
        for item in payload.get("results", [])[:max_results]:
            title = item.get("title") or "Untitled source"
            documents.append(
                SourceDocument(
                    title=title,
                    url=item.get("url"),
                    snippet=clean_search_snippet(item.get("content") or "", title),
                    metadata={"provider": "tavily", "score": item.get("score")},
                )
            )
        return documents
