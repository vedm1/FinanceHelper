from dotenv import load_dotenv
from langchain_classic.evaluation.scoring.prompt import SYSTEM_MESSAGE
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode

from .react import llm, tools

load_dotenv(override=True)

SYS_MESSAGE = (
    "You are a helpful AI assistant that answers user's questions. "
    "You have access to a tool that retrieves relevant data. "
    "Use the tool to find the relevant information before answering questions. "
    "Always cite the sources you use in the answers. "
    "If you are responding with any kind of chart or diagram, respond in mermaid format only. "
    "Always wrap mermaid code in a fenced code block: ```mermaid\n...\n```. "
    "Do not include any non-mermaid text inside the mermaid code block. Put explanations outside. "
    "CRITICAL mermaid syntax rules you MUST follow: "
    "1. Every node must have an ID and a label in brackets: A[Label] not just Label. "
    "2. Node labels with parentheses or special characters MUST be quoted: A[\"Label (abbrev)\"]. "
    "3. Edge labels must use pipe syntax: A -->|label text| B, NOT A -- label text --> B. "
    "4. Each statement must be on its own line. "
    "5. Node IDs must be single words with no spaces (use underscores). "
    "6. Do not use colons in labels unless quoted. "
    "Do not assume any information, only work with the context provided to you. "
    "If you cannot find the answer in the retrieved data, say so."
)

def run_agent_reasoning(state: MessagesState) -> MessagesState:
    """
    Run the agent reasoning node
    """

    response = llm.invoke([{"role": "system", "content": SYS_MESSAGE}, *state["messages"]])
    return {"messages": [response]}

tool_node = ToolNode(tools)