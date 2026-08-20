"""Local Streamlit demo for the research workflow."""

import os
import re
from html import escape
from importlib import import_module
from time import perf_counter
from typing import Any

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.services.llm_client import LLMClient, LLMResponse

st: Any = import_module("streamlit")


def _configure_page() -> None:
    st.set_page_config(
        page_title="ResearchFlow AI",
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .stApp {background: #f6f7fb; color: #172033;}
        .stApp h1, .stApp h2, .stApp h3, .stApp h4,
        .stApp p, .stApp label, .stApp li {color: #172033;}
        [data-testid="stSidebar"] {background: #101827;}
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            color: #f8fafc !important;
        }
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] [data-baseweb="select"] * {
            color: #172033 !important;
        }
        [data-testid="stTextArea"] textarea,
        [data-testid="stTextInput"] input {
            background: #ffffff !important;
            color: #172033 !important;
            -webkit-text-fill-color: #172033 !important;
        }
        [data-testid="stTextArea"] textarea::placeholder,
        [data-testid="stTextInput"] input::placeholder {color: #7a8699 !important;}
        .hero {padding: 2rem; border-radius: 22px; color: white;
               background: linear-gradient(120deg, #14213d, #2457d6 65%, #17a6a1);
               box-shadow: 0 16px 40px rgba(20, 33, 61, .18); margin-bottom: 1.2rem;}
        .hero h1 {margin: 0; font-size: 2.35rem; letter-spacing: -.04em;
                  color: #ffffff !important;}
        .hero p {margin: .55rem 0 0; color: #dce8ff !important; max-width: 760px;}
        .flow {display:flex; align-items:center; flex-wrap:wrap; gap:.5rem; margin:.4rem 0 1rem;}
        .node {background:white; border:1px solid #dce3f0; border-radius:999px;
               padding:.45rem .8rem; font-weight:700; color:#233557;}
        .arrow {color:#7290bd; font-weight:800;}
        .source {background:white; border:1px solid #e1e7f0; border-radius:14px;
                 padding:1rem; margin:.6rem 0;}
        .source a {font-weight:700; color:#2457d6; text-decoration:none;}
        .muted {color:#667085; font-size:.9rem;}
        [data-testid="stMetric"] {background:white; border:1px solid #e1e7f0;
                                  border-radius:14px; padding:.8rem 1rem;}
        [data-testid="stMetric"] * {color:#172033 !important;}
        .stTabs [data-baseweb="tab"] {color:#344563;}
        .stTabs [aria-selected="true"] {color:#2457d6 !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _configure_tracing() -> None:
    settings = get_settings()
    os.environ["LANGSMITH_TRACING"] = str(settings.langsmith_tracing).lower()
    if settings.langsmith_tracing and settings.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project


def _usage(state: ResearchState) -> tuple[int, int, float | None]:
    input_tokens = sum(int(item.metadata.get("input_tokens") or 0) for item in state.agent_results)
    output_tokens = sum(
        int(item.metadata.get("output_tokens") or 0) for item in state.agent_results
    )
    costs = [
        float(item.metadata["cost_usd"])
        for item in state.agent_results
        if item.metadata.get("cost_usd") is not None
    ]
    return input_tokens, output_tokens, sum(costs) if costs else None


def _citation_coverage(state: ResearchState) -> float:
    cited = {int(value) for value in re.findall(r"\[(\d+)\]", state.final_answer or "")}
    valid = {value for value in cited if 1 <= value <= len(state.sources)}
    return len(valid) / len(state.sources) if state.sources else 0.0


def _run_baseline(query: str) -> dict[str, Any]:
    started = perf_counter()
    response: LLMResponse = LLMClient().complete(
        "Bạn là trợ lý nghiên cứu cẩn trọng. Hãy trả lời bằng tiếng Việt, đi thẳng vào vấn đề, "
        "nêu rõ điều chưa chắc chắn và không bịa nguồn hoặc citation. Giữ nguyên tên riêng và "
        "thuật ngữ tiếng Anh quan trọng.",
        query,
    )
    return {"response": response, "latency": perf_counter() - started}


def _run_multi(query: str, max_sources: int, audience: str) -> dict[str, Any]:
    state = ResearchState(
        request=ResearchQuery(query=query, max_sources=max_sources, audience=audience)
    )
    started = perf_counter()
    result = MultiAgentWorkflow().run(state)
    return {"state": result, "latency": perf_counter() - started}


def _render_route(routes: list[str]) -> None:
    labels = {
        "researcher": "Researcher",
        "analyst": "Analyst",
        "writer": "Writer",
        "critic": "Critic",
        "done": "Hoàn tất",
    }
    parts: list[str] = []
    for index, route in enumerate(routes):
        if index:
            parts.append('<span class="arrow">→</span>')
        parts.append(f'<span class="node">{labels.get(route, route.title())}</span>')
    st.markdown(f'<div class="flow">{"".join(parts)}</div>', unsafe_allow_html=True)


def _render_sources(state: ResearchState) -> None:
    for index, source in enumerate(state.sources, 1):
        title = escape(f"[{index}] {source.title}")
        safe_url = escape(source.url or "", quote=True)
        heading = f'<a href="{safe_url}" target="_blank">{title}</a>' if source.url else title
        provider = source.metadata.get("provider", "unknown")
        score = source.metadata.get("score")
        score_text = f" · relevance {float(score):.2f}" if score is not None else ""
        st.markdown(
            f'<div class="source">{heading}<div class="muted">{provider}{score_text}</div>'
            f"<p>{escape(source.snippet)}</p></div>",
            unsafe_allow_html=True,
        )


def _render_baseline(result: dict[str, Any]) -> None:
    response: LLMResponse = result["response"]
    columns = st.columns(4)
    columns[0].metric("Thời gian", f"{result['latency']:.2f}s")
    columns[1].metric("Input tokens", response.input_tokens or 0)
    columns[2].metric("Output tokens", response.output_tokens or 0)
    columns[3].metric("Chi phí", f"${response.cost_usd:.6f}" if response.cost_usd else "N/A")
    st.subheader("Câu trả lời")
    st.markdown(response.content)


def _render_multi(result: dict[str, Any]) -> None:
    state: ResearchState = result["state"]
    input_tokens, output_tokens, cost = _usage(state)
    columns = st.columns(5)
    columns[0].metric("Thời gian", f"{result['latency']:.2f}s")
    columns[1].metric("Nguồn", len(state.sources))
    columns[2].metric("Tokens", f"{input_tokens + output_tokens:,}")
    columns[3].metric("Chi phí", f"${cost:.6f}" if cost is not None else "N/A")
    columns[4].metric("Citation", f"{_citation_coverage(state):.0%}")

    st.subheader("Luồng xử lý")
    _render_route(state.route_history)
    answer_tab, sources_tab, process_tab, trace_tab = st.tabs(
        ["Câu trả lời", "Nguồn tham khảo", "Dữ liệu trung gian", "Trace"]
    )
    with answer_tab:
        st.markdown(state.final_answer or "Chưa có câu trả lời.")
    with sources_tab:
        _render_sources(state)
    with process_tab:
        st.markdown("#### Research notes")
        st.text(state.research_notes or "")
        st.markdown("#### Analysis notes")
        st.markdown(state.analysis_notes or "")
    with trace_tab:
        st.json(
            {"route_history": state.route_history, "events": state.trace, "errors": state.errors}
        )


def main() -> None:
    _configure_page()
    _configure_tracing()
    settings = get_settings()

    with st.sidebar:
        st.title("◈ ResearchFlow")
        st.caption("Multi-Agent Research System")
        st.divider()
        mode = st.radio("Chế độ", ["Multi-Agent", "Baseline"], horizontal=True)
        max_sources = st.slider("Số nguồn tối đa", 1, 10, 5, disabled=mode == "Baseline")
        audience = st.selectbox(
            "Đối tượng đọc",
            ["người học kỹ thuật", "lãnh đạo doanh nghiệp", "độc giả phổ thông", "nhà nghiên cứu"],
            disabled=mode == "Baseline",
        )
        st.divider()
        st.caption("Trạng thái dịch vụ")
        st.write("🟢 OpenRouter" if settings.openrouter_api_key else "🔴 OpenRouter")
        st.write("🟢 Tavily" if settings.tavily_api_key else "🟡 Tavily fallback")
        st.write("🟢 LangSmith trace" if settings.langsmith_tracing else "⚪ LangSmith tắt")

    st.markdown(
        '<div class="hero"><h1>ResearchFlow AI</h1><p>Biến một câu hỏi thành nghiên cứu '
        "có nguồn, phân tích phản biện và câu trả lời có thể kiểm chứng.</p></div>",
        unsafe_allow_html=True,
    )
    query = st.text_area(
        "Câu hỏi nghiên cứu",
        value="Research GraphRAG state-of-the-art",
        height=110,
        placeholder="Nhập chủ đề bạn muốn nghiên cứu…",
    )
    run = st.button("Bắt đầu nghiên cứu", type="primary", use_container_width=True)
    if run:
        if len(query.strip()) < 5:
            st.warning("Câu hỏi cần ít nhất 5 ký tự.")
            return
        try:
            with st.status("Đang chạy hệ thống…", expanded=True) as status:
                if mode == "Baseline":
                    st.write("Đang gọi single-agent baseline…")
                    st.session_state["baseline_result"] = _run_baseline(query.strip())
                else:
                    st.write("Researcher đang tìm nguồn với Tavily…")
                    st.write("Analyst và Writer sẽ xử lý sau khi có bằng chứng…")
                    st.session_state["multi_result"] = _run_multi(
                        query.strip(), max_sources, audience
                    )
                st.session_state["last_mode"] = mode
                status.update(label="Hoàn tất nghiên cứu", state="complete", expanded=False)
        except Exception as exc:
            st.error(f"Không thể hoàn thành: {type(exc).__name__}: {exc}")

    last_mode = st.session_state.get("last_mode")
    if last_mode == "Baseline" and "baseline_result" in st.session_state:
        _render_baseline(st.session_state["baseline_result"])
    elif last_mode == "Multi-Agent" and "multi_result" in st.session_state:
        _render_multi(st.session_state["multi_result"])


if __name__ == "__main__":
    main()
