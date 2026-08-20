"""Optional critic agent skeleton for bonus work."""

import re

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings.

        Check that every numeric citation points to an available source.
        """

        answer = state.final_answer or ""
        citations = {int(value) for value in re.findall(r"\[(\d+)\]", answer)}
        invalid = sorted(value for value in citations if not 1 <= value <= len(state.sources))
        uncited = not citations and bool(answer)
        findings = (
            f"invalid_citations={invalid}; "
            f"citation_present={not uncited}; source_count={len(state.sources)}"
        )
        state.agent_results.append(AgentResult(agent=AgentName.CRITIC, content=findings))
        state.add_trace_event("critic", {"invalid_citations": invalid, "uncited": uncited})
        return state
