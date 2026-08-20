# Benchmark Report: Single-Agent vs Multi-Agent GraphRAG Research

## Experiment

- Date: 2026-08-20
- Query: `Research GraphRAG state-of-the-art`
- LLM provider: OpenRouter
- Model: `openai/gpt-4o-mini`
- Search provider: Tavily (multi-agent only)
- Multi-agent route: `researcher → analyst → writer → done`
- Runs per approach: 1 (smoke benchmark; not statistically significant)

## Results

| Run | LLM latency (s) | Input tokens | Output tokens | Total tokens | Cost (USD) | Quality | Citation coverage | Failure rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Single-agent baseline | 6.60 | 37 | 234 | 271 | 0.000146 | 3/10 | N/A | 0% |
| Multi-agent | 27.48 | 2,346 | 1,837 | 4,183 | 0.001454 | 8/10 | 100% (5/5) | 0% |

The multi-agent latency is the sum of the measured Analyst and Writer LLM calls
(14.11 + 13.37 seconds). Search time was not separately recorded, so the full wall-clock latency
is slightly higher. Cost is the provider-reported cost for multi-agent and a model-rate estimate
for baseline (`$0.15/M` input tokens and `$0.60/M` output tokens).

## Quality assessment

Quality was manually scored from 0–10 using four dimensions: relevance and currency (3 points),
evidence and citations (3 points), critical analysis (2 points), and clarity/completeness (2 points).

### Single-agent baseline — 3/10

The baseline is readable and gives a broadly correct definition, but it states that its knowledge
ends in October 2023, provides no current research findings, names no concrete GraphRAG methods or
results, and contains no verifiable citations. This is especially weak for a state-of-the-art query.

### Multi-agent — 8/10

The multi-agent answer uses five retrieved sources, cites all five, compares claims, discusses
source reliability, and flags missing advanced-RAG comparisons and weakly contextualized token
reduction claims. It is much more useful for the requested research task. Points were deducted
because one Medium source is weak, the Analyst labels the arXiv survey as peer-reviewed without
verification, and some claims are repetitive.

## Cost and latency trade-off

Compared with baseline, multi-agent used about 15.4× as many tokens, cost about 10× more, and spent
about 4.2× longer in LLM calls. For a simple definition this overhead would not be justified. For a
current research query, however, the baseline cannot supply evidence or current findings, while the
multi-agent workflow produces traceable sources and explicit uncertainty analysis.

## Citation coverage

The final multi-agent answer references `[1]` through `[5]`, and every reference maps to an item in
`state.sources`, giving 5/5 (100%) source-level citation coverage. This metric checks citation
presence and validity, not whether every sentence is entailed by its cited source. The baseline has
no retrieved source set, so citation coverage is reported as N/A rather than 0%.

## Failure modes

1. **Incorrect source classification:** the Analyst treated an arXiv preprint as peer-reviewed.
   Add source-type metadata and require the Analyst to call preprints “not peer-reviewed unless
   verified.”
2. **Uneven source quality:** a Medium implementation article received similar attention to an
   academic survey and official Microsoft documentation. Add domain/type-based ranking and prefer
   primary or peer-reviewed sources.
3. **Snippet-only evidence:** analysis currently relies on Tavily snippets, which can omit important
   context. Fetch and parse source pages for high-impact claims before writing.
4. **Encoding artifacts:** text such as `â€™` can appear in some Windows terminal captures. Run
   PowerShell with UTF-8 (`chcp 65001` and `PYTHONUTF8=1`) and normalize retrieved text.
5. **Small sample size:** one query and one run cannot establish general superiority. Repeat each
   configured query at least three times and report mean, median, and error bars.

## Trace evidence

The shared state recorded four routing decisions and three worker events, ending with `errors: []`.
OpenRouter returned HTTP 200 for both LLM calls. LangSmith authentication was separately verified;
with `LANGSMITH_TRACING=true`, LangGraph can upload the node-level execution trace to the configured
project.

## Conclusion

For this evidence-heavy, time-sensitive query, multi-agent execution is the better design despite
its higher latency and cost. The baseline remains preferable for short, stable questions where web
research, source comparison, and citation traceability are unnecessary.
