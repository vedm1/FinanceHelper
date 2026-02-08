from typing import Any, Dict

from graph.chains.retrieval_grader import retrieval_grader
from graph.state import GraphState

def grade_documents(state: GraphState) -> Dict[str, Any]:
    """
    Determines whether the retrieved documents are relevant to the user's question.
    If any question is not relevant, we will set a flag to run web search.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Filtered out irrelevant documents and the updated web_search state
    """
    print("---Check Document Relevance---")
    question = state["question"]
    documents = state["documents"]

    filtered_documents = []
    web_search = False
    for document in documents:
        score = retrieval_grader.invoke(
            {"question": question, "document": document}
        )
        grade = score.binary_score
        if grade.lower() == "yes":
            print("---Grade: Document is relevant---")
            filtered_documents.append(document)
        else:
            print("---Grade: Document is irrelevant---")
            web_search = True
            continue

    return {"documents": filtered_documents, "question": question, "web_search": web_search}