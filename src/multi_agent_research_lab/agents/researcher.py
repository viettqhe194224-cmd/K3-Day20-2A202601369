"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`.

        Sources are deduplicated by URL/title and assigned stable citation numbers.
        """

        found = self.search_client.search(state.request.query, state.request.max_sources)
        unique = {source.url or source.title: source for source in found}
        state.sources = list(unique.values())[: state.request.max_sources]
        state.research_notes = "\n".join(
            f"[{index}] {source.title}: {source.snippet}"
            for index, source in enumerate(state.sources, 1)
        )
        state.agent_results.append(
            AgentResult(agent=AgentName.RESEARCHER, content=state.research_notes)
        )
        state.add_trace_event("researcher", {"source_count": len(state.sources)})
        return state

    def __init__(self, search_client: SearchClient | None = None) -> None:
        self.search_client = search_client or SearchClient()
