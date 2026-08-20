.PHONY: install test lint format typecheck run-baseline run-multi run-ui clean

install:
	pip install -e ".[dev,llm]"

test:
	pytest

lint:
	ruff check src tests

format:
	ruff format src tests

typecheck:
	mypy src

run-baseline:
	python -m multi_agent_research_lab.cli baseline --query "Research GraphRAG state-of-the-art"

run-multi:
	python -m multi_agent_research_lab.cli multi-agent --query "Research GraphRAG state-of-the-art"

run-ui:
	streamlit run src/multi_agent_research_lab/ui.py

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache dist build *.egg-info
