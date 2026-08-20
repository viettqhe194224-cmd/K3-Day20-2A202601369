"""Benchmark skeleton for single-agent vs multi-agent."""

import re
from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, failure, citation coverage, and a transparent quality heuristic."""

    started = perf_counter()
    try:
        state = runner(query)
        failed = not bool(state.final_answer)
    except Exception as exc:
        state = ResearchState.model_validate(
            {"request": {"query": query}, "errors": [f"{type(exc).__name__}: {exc}"]}
        )
        failed = True
    latency = perf_counter() - started
    answer = state.final_answer or ""
    cited = {int(value) for value in re.findall(r"\[(\d+)\]", answer)}
    valid = {number for number in cited if 1 <= number <= len(state.sources)}
    coverage = len(valid) / len(state.sources) if state.sources else 0.0
    quality = min(10.0, len(answer.split()) / 50 + coverage * 3) if answer else 0.0
    tokens = sum(
        int(result.metadata.get(key) or 0)
        for result in state.agent_results
        for key in ("input_tokens", "output_tokens")
    )
    costs = [
        float(result.metadata["cost_usd"])
        for result in state.agent_results
        if result.metadata.get("cost_usd") is not None
    ]
    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=sum(costs) if costs else None,
        quality_score=quality,
        citation_coverage=coverage,
        failure_rate=float(failed),
        notes=f"Observed tokens: {tokens}; heuristic quality (not an LLM judge).",
    )
    return state, metrics
