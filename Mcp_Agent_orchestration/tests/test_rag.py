from rag.retriever import search_knowledge_base


def test_rag_finds_annual_leave_policy():
    result = search_knowledge_base(
        "What is the annual leave policy?",
        max_results=3,
    )

    assert result["success"] is True
    assert result["query"] == "What is the annual leave policy?"
    assert len(result["results"]) > 0

    first_result = result["results"][0]

    assert first_result["source"] == "data\\documents\\employee_policy.txt"
    assert "12 days of annual leave" in first_result["content"]
    assert isinstance(first_result["score"], float)


def test_rag_rejects_empty_query():
    result = search_knowledge_base("")

    assert result["success"] is False
    assert result["error"] == "The knowledge-base query cannot be empty."