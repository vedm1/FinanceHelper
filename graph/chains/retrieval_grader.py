from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model_name="claude-sonnet-4-5", temperature=0)

class GradeDocuments(BaseModel):
    """Binary score for relevance check on each document"""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )

structured_llm_grader = llm.with_structured_output(GradeDocuments)

system = """You are a grader assessing the relevance of documents to a user question. \n
            You will be provided with a question and a list of documents. \n
            Your task is to determine if each document is relevant to the question. \n
            Respond with 'yes' or 'no' for each document."""

grader_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}")
    ]
)

retrieval_grader = grader_prompt | structured_llm_grader