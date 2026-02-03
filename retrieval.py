import os
from operator import itemgetter

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv(override=True)

embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
llm = ChatOpenAI(model="gpt-4.1")

vectorstore = PineconeVectorStore(index_name=os.getenv("INDEX_NAME"), embedding=embeddings)

# Score threshold - only return documents with similarity >= this value
# Pinecone returns cosine similarity scores between 0 and 1 (higher = more similar)
SCORE_THRESHOLD = 0.75

# MMR lambda - balance between relevance (0) and diversity (1)
# 0.5 = equal weight, 0.7 = more diversity, 0.3 = more relevance
MMR_LAMBDA = 0.5


def retrieve_with_mmr(query: str, k: int = 20, fetch_k: int = 100) -> list:
    """
    Retrieve documents using MMR for diversity + score filtering.

    Args:
        query: Search query
        k: Number of documents to return after MMR
        fetch_k: Number of documents to fetch before applying MMR
    """
    # Use MMR to get diverse results
    # fetch_k: how many to initially retrieve
    # k: how many to return after MMR reranking
    docs = vectorstore.max_marginal_relevance_search(
        query,
        k=k,
        fetch_k=fetch_k,
        lambda_mult=MMR_LAMBDA
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


def retrieval_with_lcel():
    # Use MMR retrieval for diverse, relevant results
    mmr_retriever = RunnableLambda(
        lambda q: retrieve_with_mmr(q, k=20, fetch_k=100)
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

    # Query

    query = "Do you have any information on Ved Muthal?"

    # # =====================================================
    # # Option 1: Use the implementation without LCEL
    # # =====================================================
    #
    # print("\n" + "=" * 70)
    # print("Implementation 1: Without LCEL")
    # print("=" * 70)
    # result_without_lcel = retrieval_without_lcel(query)
    # print("\nAnswer:")
    # print(result_without_lcel)

    # =====================================================
    # Option 2: Use the implementation with LCEL
    # =====================================================

    print("\n" + "=" * 70)
    print("Implementation 1: With LCEL")
    print("=" * 70)
    chain_with_lcel = retrieval_with_lcel()
    result_with_lcel = chain_with_lcel.invoke({"question": query})
    print("\nAnswer:")
    print(result_with_lcel)