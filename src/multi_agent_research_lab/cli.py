"""Command-line entrypoint for the lab starter."""

import os
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    os.environ["LANGSMITH_TRACING"] = str(settings.langsmith_tracing).lower()
    if settings.langsmith_tracing and settings.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project


def _parse_query(query: str) -> ResearchQuery:
    try:
        return ResearchQuery(query=query)
    except ValidationError as exc:
        console.print(
            Panel.fit(
                f"Invalid query: {exc.errors()[0]['msg']}",
                title="Input Error",
                style="red",
            )
        )
        raise typer.Exit(code=1) from exc


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a single end-to-end LLM call."""

    _init()
    request = _parse_query(query)
    response = LLMClient().complete(
        "Bạn là trợ lý nghiên cứu cẩn trọng. Hãy trả lời bằng tiếng Việt, đi thẳng vào vấn đề, "
        "nêu rõ điều chưa chắc chắn và không bịa nguồn hoặc citation. Giữ nguyên tên riêng và "
        "thuật ngữ tiếng Anh quan trọng.",
        request.query,
    )
    console.print(Panel.fit(response.content, title="Single-Agent Baseline"))
    console.print(
        {
            "latency_seconds": response.latency_seconds,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
        }
    )


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()
    state = ResearchState(request=_parse_query(query))
    workflow = MultiAgentWorkflow()
    try:
        result = workflow.run(state)
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    console.print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
