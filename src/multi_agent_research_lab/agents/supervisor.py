"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self, max_iterations: int | None = None) -> None:
        self.max_iterations = max_iterations or get_settings().max_iterations

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route.

        Routes through missing artifacts in order and enforces a hard iteration cap.
        """

        if state.iteration >= self.max_iterations or state.final_answer:
            route = "done"
        elif not state.sources or not state.research_notes:
            route = "researcher"
        elif not state.analysis_notes:
            route = "analyst"
        else:
            route = "writer"
        state.record_route(route)
        state.add_trace_event("route", {"next": route, "iteration": state.iteration})
        return state
