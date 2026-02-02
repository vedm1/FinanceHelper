import os
from operator import itemgetter

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv(override=True)

embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(model="gpt-4.1")

vectorstores = PineconeVectorStore(index_name=os.getenv("INDEX_NAME"), embedding=embeddings)

retriever = vectorstores.as_retriever(search_kwargs={"k": 100})

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
    docs = retriever.invoke(query)

    context = format_docs(docs)

    messages = prompt_template.format_messages(context=context, question=query)

    response = llm.invoke(messages)

    return response.content


def retrieval_with_lcel():
    retrieval_chain = (
            RunnablePassthrough.assign(
                context=itemgetter("question") | retriever | format_docs
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