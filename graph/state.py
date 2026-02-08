from typing import Any, Dict, List, Optional, TypedDict


class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        web_search: whether to perform web search
        documents: list of documents
        owner: optional filter by owner
        company: optional filter by company
        category: optional filter by category
        year: optional filter by year

    """

    question: str
    generation: str
    web_search: bool
    documents: List[str]
    owner: Optional[str]
    company: Optional[str]
    category: Optional[str]
    year: Optional[int]
