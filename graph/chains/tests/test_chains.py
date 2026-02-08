from dotenv import load_dotenv
load_dotenv(override=True)

from graph.chains.retrieval_grader import GradeDocuments, retrieval_grader
from retrieval import retrieve_with_mmr
from pprint import pprint
from graph.chains.generation import generation_chain

def test_foo() -> None:
    assert 1 == 1

def test_retrieval_grader_answer_yes() -> None:
    question = "What are the different brand share types a user can select?"
    document = retrieve_with_mmr(question)
    doc_txt = document[0].page_content

    result: GradeDocuments = retrieval_grader.invoke(
        {
            "question": question, "document": doc_txt
        }
    )

    assert result.binary_score == "yes"

def test_retrieval_grader_answer_no() -> None:
    question = "How to make Pizza"
    document = retrieve_with_mmr(question)
    doc_txt = document[0].page_content

    result: GradeDocuments = retrieval_grader.invoke(
        {
            "question": question, "document": doc_txt
        }
    )

    assert result.binary_score == "no"

def test_generation_chain() -> None:
    question = "What is the capital of India?"
    documents = retrieve_with_mmr(question)
    generation = generation_chain.invoke({"question": question, "context": documents})
    pprint(generation)