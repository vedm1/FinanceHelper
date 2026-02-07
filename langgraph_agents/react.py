import os
import sys

from dotenv import load_dotenv
from langchain_core.tools import tool, StructuredTool
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import ToolNode

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from retrieval import search_documents
from .schemas import AnswerQuestion, ReviseAnswer


load_dotenv()

@tool
def triple(num: float) -> float:
    """
    param num: a number to triple
    returns: the triple value of the input number
    """
    return float(num) ** 3

tools = [search_documents, triple]

def run_queries(search_queries: list[str], **kwargs):
    """Execute search queries against the document store and return results."""
    return "\n\n".join(search_documents.invoke(query) for query in search_queries)

execute_tools = ToolNode(
    [
        StructuredTool.from_function(run_queries, name=AnswerQuestion.__name__),
        StructuredTool.from_function(run_queries, name=ReviseAnswer.__name__)

    ]
)

# llm = ChatOpenAI(model="gpt-4.1", temperature=0).bind_tools(tools)
llm = ChatAnthropic(model_name="claude-sonnet-4-5", temperature=0).bind_tools(tools)



