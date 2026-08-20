"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass
from time import perf_counter

from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import Settings, get_settings


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    latency_seconds: float | None = None


class LLMClient:
    """OpenAI-compatible client supporting OpenAI and OpenRouter."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion.

        Provider selection is automatic: OpenRouter takes precedence when configured.
        """

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError('Install LLM dependencies with: pip install -e ".[llm]"') from exc

        if self.settings.openrouter_api_key:
            api_key = self.settings.openrouter_api_key
            model = self.settings.openrouter_model
            base_url = "https://openrouter.ai/api/v1"
        elif self.settings.openai_api_key:
            api_key = self.settings.openai_api_key
            model = self.settings.openai_model
            base_url = None
        else:
            raise RuntimeError("Set OPENROUTER_API_KEY or OPENAI_API_KEY in .env")

        client = OpenAI(api_key=api_key, base_url=base_url, timeout=self.settings.timeout_seconds)
        started = perf_counter()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        usage = response.usage
        usage_extra = usage.model_extra if usage and usage.model_extra else {}
        return LLMResponse(
            content=response.choices[0].message.content or "",
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
            cost_usd=usage_extra.get("cost"),
            latency_seconds=perf_counter() - started,
        )
