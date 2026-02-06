import os
from operator import itemgetter

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from typing import Optional

from graph_manager import GraphManager

load_dotenv(override=True)

embeddings = OpenAIEmbeddings(model="text-embedding-3-large", openai_api_key=os.getenv("OPENAI_API_KEY"))
llm = ChatOpenAI(model="gpt-4.1")

vectorstore = PineconeVectorStore(index_name=os.getenv("INDEX_NAME"), embedding=embeddings)

# Score threshold - only return documents with similarity >= this value
# Pinecone returns cosine similarity scores between 0 and 1 (higher = more similar)
SCORE_THRESHOLD = 0.75

# MMR lambda - balance between relevance (0) and diversity (1)
# 0.5 = equal weight, 0.7 = more diversity, 0.3 = more relevance
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

    Args:
        query: Search query
        k: Number of documents to return after MMR
        fetch_k: Number of documents to fetch before applying MMR
        owner: Filter to documents belonging to this owner
        company: Filter to documents from this company
        category: Filter to documents in this category
        year: Filter to documents from this year
    """
    # If filters are provided, get allowed sources from graph
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
            return []  # No documents match the filters

        # Pinecone filter: only search within allowed sources
        filter_dict = {"source": {"$in": allowed_sources}}

    # Use MMR to get diverse results
    docs = vectorstore.max_marginal_relevance_search(
        query,
        k=k,
        fetch_k=fetch_k,
        lambda_mult=MMR_LAMBDA,
        filter=filter_dict,
    )

    return docs


def retrieve_with_score_filter(query: str, k: int = 100) -> list:
    """Retrieve documents that meet the similarity score threshold."""
    # Get documents with their similarity scores
    docs_with_scores = vectorstore.similarity_search_with_score(query, k=k)

    # Filter by score threshold (Pinecone: higher score = more similar)
    filtered_docs = [
        doc for doc, score in docs_with_scores
        if score >= SCORE_THRESHOLD
    ]

    return filtered_docs


# Keep the basic retriever for backward compatibility
retriever = vectorstore.as_retriever(search_kwargs={"k": 100})

prompt_template = ChatPromptTemplate.from_template(
    """Answer the question based only on the following context:

    {context}

    Question: {question}

    Provide a detailed answer:"""
)


def format_docs(docs):
    """Format retrieved documents into a single string"""
    return "\n\n ".join(doc.page_content for doc in docs)


def retrieval_without_lcel(query: str):
    # Use score-filtered retrieval instead of basic retriever
    docs = retrieve_with_score_filter(query, k=100)

    if not docs:
        return "No relevant documents found for your query."

    context = format_docs(docs)

    messages = prompt_template.format_messages(context=context, question=query)

    response = llm.invoke(messages)

    return response.content

@tool
def search_documents(query: str) -> str:
    """Search the knowledge base for relevant information to answer a user's question.

    Args:
        query: The search query to find relevant documents
    """
    docs = retrieve_with_mmr(query, k=20, fetch_k=100)
    if not docs:
        return "No relevant documents found."
    return "\n\n".join(
        f"Source: {doc.metadata.get('source', 'Unknown')}\nContent: {doc.page_content}"
        for doc in docs
    )


def retrieval_with_lcel(
    owner: Optional[str] = None,
    company: Optional[str] = None,
    category: Optional[str] = None,
    year: Optional[int] = None,
):
    """
    Create an LCEL retrieval chain with optional graph-based filtering.

    Args:
        owner: Filter to documents belonging to this owner
        company: Filter to documents from this company
        category: Filter to documents in this category
        year: Filter to documents from this year
    """
    # Use MMR retrieval with graph filters
    mmr_retriever = RunnableLambda(
        lambda q: retrieve_with_mmr(
            q, k=20, fetch_k=100,
            owner=owner, company=company, category=category, year=year
        )
    )

    retrieval_chain = (
            RunnablePassthrough.assign(
                context=itemgetter("question") | mmr_retriever | format_docs
            )
            | prompt_template
            | llm
            | StrOutputParser()
    )
    return retrieval_chain


if __name__ == "__main__":
    print("Retrieving documents...")

    # =====================================================
    # Example 1: Unfiltered query (searches all documents)
    # =====================================================
    print("\n" + "=" * 70)
    print("Example 1: Unfiltered search")
    print("=" * 70)

    query = "What is the PAN number?"
    chain = retrieval_with_lcel()
    result = chain.invoke({"question": query})
    print(f"\nQuery: {query}")
    print(f"Answer: {result}")

    # =====================================================
    # Example 2: Filtered to personal documents only
    # =====================================================
    print("\n" + "=" * 70)
    print("Example 2: Filtered to Ved Muthal's documents only")
    print("=" * 70)

    query = "What personal information do you have?"
    chain = retrieval_with_lcel(owner="Ved Muthal")
    result = chain.invoke({"question": query})
    print(f"\nQuery: {query}")
    print(f"Filter: owner='Ved Muthal'")
    print(f"Answer: {result}")

    # =====================================================
    # Example 3: Filtered to SBI documents from 2024
    # =====================================================
    print("\n" + "=" * 70)
    print("Example 3: Filtered to SBI 2024 documents")
    print("=" * 70)

    query = "What was the net profit?"
    chain = retrieval_with_lcel(company="State Bank of India", year=2024)
    result = chain.invoke({"question": query})
    print(f"\nQuery: {query}")
    print(f"Filter: company='State Bank of India', year=2024")
    print(f"Answer: {result}")