from typing import Any, Dict
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_tavily import TavilySearch

from graph.state import GraphState

load_dotenv(override=True)

web_search_tool = TavilySearch(max_results=3)


def web_search(state: GraphState) -> Dict[str, Any]:
    """
    Performs a web search to find additional documents related to the user's question.
    """
    print("---Web Search---")
    question = state["question"]
    documents = state["documents"]

    tavily_results = web_search_tool.invoke({"query": question})
    joined_tavily_results = "\n\n".join(
        [tavily_result["content"] for tavily_result in tavily_results]
    )
    web_results = Document(page_content=joined_tavily_results)
    if documents is not None:
        documents.append(web_results)
    else:
        documents = [web_results]
    return {"documents": documents, "question": question}


if __name__ == "__main__":
    web_search({"question": "What is the capital of India?", "documents": None})