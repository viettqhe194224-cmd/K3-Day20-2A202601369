"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`.

        Synthesize a clear response using only supplied evidence and [n] citations.
        """

        source_list = "\n".join(
            f"[{index}] {source.title} - {source.url or 'no URL'}"
            for index, source in enumerate(state.sources, 1)
        )
        response = self.llm_client.complete(
            "Bạn là người viết báo cáo nghiên cứu. Hãy viết câu trả lời bằng tiếng Việt rõ ràng, "
            "phù hợp với đối tượng được yêu cầu; giữ nguyên tên riêng và thuật ngữ tiếng Anh quan "
            "trọng. Trích dẫn luận điểm thực tế bằng [n], tuyệt đối không bịa citation, và kết "
            "thúc bằng mục 'Nguồn tham khảo'.",
            f"Câu hỏi: {state.request.query}\nĐối tượng đọc: {state.request.audience}\n\n"
            f"Phân tích:\n{state.analysis_notes or ''}\n\nNguồn hiện có:\n{source_list}",
        )
        state.final_answer = response.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event("writer", {"latency_seconds": response.latency_seconds})
        return state

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()
