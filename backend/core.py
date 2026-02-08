import os
import sys
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import ToolMessage
from langchain.tools import tool
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from graph_manager import GraphManager

load_dotenv(override=True)

embeddings = OpenAIEmbeddings(model="text-embedding-3-large", openai_api_key=os.getenv("OPENAI_API_KEY"))

vectorstore = PineconeVectorStore(index_name=os.getenv("INDEX_NAME"), embedding=embeddings)

# model = init_chat_model("gpt-4.1", model_provider="openai")

model = init_chat_model("claude-sonnet-4-5", model_provider="anthropic")

# Retrieval settings
SCORE_THRESHOLD = 0.75
MMR_LAMBDA = 0.5

def retrieve_with_mmr(
    query: str,
    k: int = 20,
    fetch_k: int = 100,
    owner: Optional[str] = None,
    company: Optional[str] = None,
    category: Optional[str] = None,
    year: Optional[int] = None,
) -> list:
    """
    Retrieve documents using MMR for diversity, with optional graph-based filtering.
    """
    filter_dict = None
    if any([owner, company, category, year]):
        with GraphManager() as gm:
            allowed_sources = gm.query_documents(
                owner=owner,
                company=company,
                category=category,
                year=year,
            )

        if not allowed_sources:
            return []

        filter_dict = {"source": {"$in": allowed_sources}}

    docs = vectorstore.max_marginal_relevance_search(
        query,
        k=k,
        fetch_k=fetch_k,
        lambda_mult=MMR_LAMBDA,
        filter=filter_dict,
    )

    return docs


# Store current filter context for the tool
_current_filters: Dict[str, Any] = {}


@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve relevant information to help answer a user's queries"""
    retrieved_data = retrieve_with_mmr(
        query,
        k=20,
        fetch_k=100,
        owner=_current_filters.get("owner"),
        company=_current_filters.get("company"),
        category=_current_filters.get("category"),
        year=_current_filters.get("year"),
    )

    serialized_data = "\n\n".join(
        f"Source: {doc.metadata.get('source', 'Unknown')}\n\nContent: {doc.page_content}" for doc in retrieved_data
    )

    return serialized_data, retrieved_data

def run_llm(
    query: str,
    owner: Optional[str] = None,
    company: Optional[str] = None,
    category: Optional[str] = None,
    year: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run the RAG pipeline to answer a query using retrieved documentation.

    Args:
        query: The user's question
        owner: Filter to documents belonging to this owner
        company: Filter to documents from this company
        category: Filter to documents in this category
        year: Filter to documents from this year

    Returns:
        Dictionary containing:
            - answer: The generated answer
            - context: List of retrieved documents
    """
    global _current_filters
    _current_filters = {
        "owner": owner,
        "company": company,
        "category": category,
        "year": year,
    }

    system_prompt = (
        "You are a helpful AI assistant that answers user's questions. "
        "You have access to a tool that retrieves relevant data. "
        "Use the tool to find the relevant information before answering questions. "
        "Always cite the sources you use in the answers. "
        "If you're responding an API Spec, use a standard JSON or Swagger format only."
        "If you are responding with any kind of chart or diagram, respond in mermaid format only. "
        "Always wrap mermaid code in a fenced code block: ```mermaid\\n...\\n```. "
        "Do not include any non-mermaid text inside the mermaid code block. Put explanations outside. "
        "CRITICAL mermaid syntax rules you MUST follow: "
        "1. Every node must have an ID and a label in brackets: A[Label] not just Label. "
        "2. Node labels with parentheses or special characters MUST be quoted: A[\"Label (abbrev)\"]. "
        "3. Edge labels must use pipe syntax: A -->|label text| B, NOT A -- label text --> B. "
        "4. Each statement must be on its own line. "
        "5. Node IDs must be single words with no spaces (use underscores). "
        "6. Do not use colons in labels unless quoted. "
        "Do not assume any information, only work with the context provided to you"
        "If you cannot find the answer in the retrieved data, say so."
    )

    agent = create_agent(model=model, system_prompt=system_prompt, tools=[retrieve_context])

    messages = [{"role": "user", "content": query}]

    response = agent.invoke({"messages": messages})

    answer = response["messages"][-1].content

    context_docs = []

    for message in response["messages"]:
        if isinstance(message, ToolMessage) and hasattr(message, "artifact"):
            if isinstance(message.artifact, list):
                context_docs.append(message.artifact)

    return {"answer": answer, "context": context_docs}

def run_langgraph(
    query: str,
    owner: Optional[str] = None,
    company: Optional[str] = None,
    category: Optional[str] = None,
    year: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run the LangGraph RAG pipeline: Retrieve → Grade Documents → (Web Search) → Generate.

    Args:
        query: The user's question
        owner: Filter to documents belonging to this owner
        company: Filter to documents from this company
        category: Filter to documents in this category
        year: Filter to documents from this year

    Returns:
        Dictionary containing:
            - answer: The generated answer
            - context: List of retrieved documents
    """
    from graph.graph import graph as langgraph_app

    result = langgraph_app.invoke({
        "question": query,
        "owner": owner,
        "company": company,
        "category": category,
        "year": year,
    })

    return {
        "answer": result.get("generation", "(No answer received)"),
        "context": result.get("documents", []),
    }


if __name__ == '__main__':
    # Test with owner filter
    print("=" * 70)
    print("Test: Filtered to Ved Muthal's documents")
    print("=" * 70)
    result = run_llm("What personal information do you have?", owner="Ved Muthal")
    print(f"Answer: {result['answer']}\n")

    # Test with company and year filter
    print("=" * 70)
    print("Test: Filtered to SBI 2024 documents")
    print("=" * 70)
    result = run_llm("What was the net profit?", company="State Bank of India", year=2024)
    print(f"Answer: {result['answer']}")