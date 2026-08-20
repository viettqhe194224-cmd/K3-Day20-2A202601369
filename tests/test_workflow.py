from multi_agent_research_lab.agents import AnalystAgent, ResearcherAgent, WriterAgent
from multi_agent_research_lab.core.schemas import ResearchQuery, SourceDocument
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.services.llm_client import LLMResponse


class FakeLLMClient:
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        del system_prompt, user_prompt
        return LLMResponse(content="Evidence-based result [1].", input_tokens=10, output_tokens=5)


class FakeSearchClient:
    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        del query, max_results
        return [SourceDocument(title="Test source", url="https://example.com", snippet="Fact")]


def test_workflow_runs_end_to_end_with_injected_clients() -> None:
    workflow = MultiAgentWorkflow()
    workflow.researcher = ResearcherAgent(FakeSearchClient())  # type: ignore[arg-type]
    workflow.analyst = AnalystAgent(FakeLLMClient())  # type: ignore[arg-type]
    workflow.writer = WriterAgent(FakeLLMClient())  # type: ignore[arg-type]
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))

    result = workflow.run(state)

    assert result.final_answer == "Evidence-based result [1]."
    assert result.route_history == ["researcher", "analyst", "writer", "done"]
    assert result.research_notes
    assert result.analysis_notes
