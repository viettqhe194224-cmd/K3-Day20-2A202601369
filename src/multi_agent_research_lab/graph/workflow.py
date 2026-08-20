"""LangGraph workflow skeleton."""

from typing import Any

from multi_agent_research_lab.agents import (
    AnalystAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.core.state import ResearchState


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def __init__(self, supervisor: SupervisorAgent | None = None) -> None:
        self.supervisor = supervisor or SupervisorAgent()
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()

    def build(self) -> Any:
        """Create a LangGraph graph.

        Nodes are connected through conditional routing and a bounded supervisor loop.
        """

        try:
            from langgraph.graph import END, StateGraph
        except ImportError as exc:
            raise RuntimeError('Install dependencies with: pip install -e ".[llm]"') from exc
        graph = StateGraph(ResearchState)
        graph.add_node("supervisor", self.supervisor.run)
        graph.add_node("researcher", self.researcher.run)
        graph.add_node("analyst", self.analyst.run)
        graph.add_node("writer", self.writer.run)
        graph.set_entry_point("supervisor")
        graph.add_conditional_edges(
            "supervisor",
            lambda state: state.route_history[-1],
            {"researcher": "researcher", "analyst": "analyst", "writer": "writer", "done": END},
        )
        for worker in ("researcher", "analyst", "writer"):
            graph.add_edge(worker, "supervisor")
        return graph

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state.

        The returned mapping is validated back into the public state schema.
        """

        result = (
            self.build()
            .compile()
            .invoke(state, config={"recursion_limit": self.supervisor.max_iterations * 2 + 2})
        )
        return result if isinstance(result, ResearchState) else ResearchState.model_validate(result)
