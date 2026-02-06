import os
import sys

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from retrieval import search_documents


load_dotenv()

@tool
def triple(num: float) -> float:
    """
    param num: a number to triple
    returns: the triple value of the input number
    """
    return float(num) ** 3

tools = [search_documents, triple]

# llm = ChatOpenAI(model="gpt-4.1", temperature=0).bind_tools(tools)
llm = ChatAnthropic(model_name="claude-sonnet-4-5", temperature=0).bind_tools(tools)



