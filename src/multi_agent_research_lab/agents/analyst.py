"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`.

        Extract key claims, compare viewpoints, and explicitly flag weak evidence.
        """

        response = self.llm_client.complete(
            "Bạn là chuyên gia phân tích nghiên cứu nghiêm ngặt. Hãy trả lời bằng tiếng Việt, "
            "nhưng giữ nguyên tên riêng và thuật ngữ tiếng Anh khi dịch có thể gây mất nghĩa. "
            "So sánh các luận điểm, đánh giá độ tin cậy của nguồn, chỉ ra bất đồng và đánh dấu "
            "rõ bằng chứng chưa được hỗ trợ. Giữ nguyên citation dạng [n].",
            f"Câu hỏi: {state.request.query}\n\nGhi chú nghiên cứu:\n{state.research_notes or ''}",
        )
        state.analysis_notes = response.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.ANALYST,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event("analyst", {"latency_seconds": response.latency_seconds})
        return state

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()
