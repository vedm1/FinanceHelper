from typing import Any, Dict

from graph.chains.generation import generation_chain
from graph.state import GraphState

def generate(state: GraphState) -> Dict[str, Any]:
    print("---Generate---")
    question = state['question']
    documents = state['documents']

    generation = generation_chain.invoke({"question": question, "context": documents})
    return {"documents": documents, "question": question, "generation": generation}


