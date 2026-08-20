"""Skeleton guard test.

NOTE(student): Test này chỉ xác nhận skeleton còn nguyên TODO. Sau khi bạn implement
SupervisorAgent, test này SẼ FAIL - đó là điều bình thường. Hãy xóa hoặc thay thế nó
bằng unit test thật cho routing policy của bạn.
"""

from multi_agent_research_lab.agents import SupervisorAgent
from multi_agent_research_lab.core.schemas import ResearchQuery, SourceDocument
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_routes_missing_artifacts_in_order() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    supervisor = SupervisorAgent(max_iterations=6)
    supervisor.run(state)
    assert state.route_history[-1] == "researcher"
    state.sources.append(SourceDocument(title="Source", snippet="Evidence"))
    state.research_notes = "Evidence [1]"
    supervisor.run(state)
    assert state.route_history[-1] == "analyst"
    state.analysis_notes = "Analysis [1]"
    supervisor.run(state)
    assert state.route_history[-1] == "writer"
