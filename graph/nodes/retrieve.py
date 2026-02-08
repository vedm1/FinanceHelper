from typing import Any, Dict


from graph.state import GraphState
from retrieval import retrieve_with_mmr

def retrieve(state: GraphState) -> Dict[str, Any]:
    print("---Retrieve---")
    question = state['question']

    documents = retrieve_with_mmr(
        question,
        owner=state.get("owner"),
        company=state.get("company"),
        category=state.get("category"),
        year=state.get("year"),
    )
    return {"documents": documents, "question": question}