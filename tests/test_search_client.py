from multi_agent_research_lab.services.search_client import clean_search_snippet


def test_clean_search_snippet_removes_page_chrome_and_html_entities() -> None:
    raw = """Sign up
Sign in
Unknown user
# State-of-the-Art GraphRAG
—
1
Listen
Share
## From Research to Production Reality
Useful evidence.&#x20;
"""

    result = clean_search_snippet(raw, "State-of-the-Art GraphRAG")

    assert "Sign up" not in result
    assert "Unknown user" not in result
    assert "&#x20;" not in result
    assert "From Research to Production Reality" in result
    assert "Useful evidence." in result
