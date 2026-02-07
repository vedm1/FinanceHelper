from typing import TypedDict, Annotated, Literal

from dotenv import load_dotenv

from langchain_classic.agents import Agent
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, ToolMessage
from langchain_core.messages.tool import tool_call
from langgraph.graph.message import add_messages

from langgraph.graph import StateGraph, MessagesState, START, END

from .chains import revisor, first_responder
from .react import execute_tools
from .schemas import AnswerQuestion, ReviseAnswer
max_iterations = 2


# from .nodes import run_agent_reasoning, tool_node

load_dotenv(override=True)

LAST = -1

def draft_node(state:MessagesState):
    """Draft the initial response"""
    response = first_responder.invoke({"messages": state["messages"]})
    return {"messages": [response]}

def revise_node(state:MessagesState):
    """Revise the answer based on tool results"""
    response = revisor.invoke({"messages": state["messages"]})
    return {"messages": [response]}

def event_loop(state:MessagesState) -> Literal["execute_tools", END]:
    """Determine whether to continue or end based on iteration count"""
    count_tool_visits = sum(isinstance(item, ToolMessage) for item in state["messages"])
    num_iterations = count_tool_visits
    if num_iterations > max_iterations:
        return END
    return "execute_tools"

builder = StateGraph(MessagesState)
builder.add_node("draft", draft_node)
builder.add_node("revise", revise_node)
builder.add_node("execute_tools", execute_tools)

builder.add_edge(START, "draft")
builder.add_edge("draft", "execute_tools")
builder.add_edge("execute_tools", "revise")
builder.add_conditional_edges("revise", event_loop, ["execute_tools", END])
graph = builder.compile()

print(graph.get_graph().draw_mermaid())

# class MessageGraph(TypedDict):
#     messages: Annotated[list[BaseMessage], add_messages]

# REFLECT = "reflect"
# GENERATE = "generate"
# TOOLS = "tools"
#
# def is_empty_content(content):
#     """Check if content is empty (None, empty string, or empty list)."""
#     if content is None:
#         return True
#     if isinstance(content, str) and not content.strip():
#         return True
#     if isinstance(content, list) and len(content) == 0:
#         return True
#     return False
#
# def ensure_content(messages):
#     """Ensure all messages have non-empty content for Anthropic API compatibility."""
#     fixed = []
#     for i, msg in enumerate(messages):
#         content = msg.content
#         if is_empty_content(content):
#             if hasattr(msg, 'tool_calls') and msg.tool_calls:
#                 # Rebuild AIMessage with placeholder content
#                 msg = AIMessage(
#                     content="Calling tool...",
#                     tool_calls=msg.tool_calls,
#                     id=getattr(msg, 'id', None)
#                 )
#             elif isinstance(msg, HumanMessage):
#                 # Skip empty HumanMessages (bad reflection output)
#                 print(f"Skipping empty HumanMessage at index {i}")
#                 continue
#             else:
#                 print(f"Warning: Message {i} ({type(msg).__name__}) has empty content")
#         fixed.append(msg)
#     return fixed
#
# def generation_node(state: MessageGraph):
#     messages = ensure_content(state["messages"])
#     return {"messages": [generate_chain.invoke({"messages": messages})]}
#
# def reflection_node(state: MessageGraph):
#     response = reflect_chain.invoke({"messages": state["messages"]})
#     content = response.content
#     # Handle empty content from reflection
#     if is_empty_content(content):
#         content = "Please review and improve the response."
#     return {"messages": [HumanMessage(content=content)]}
#
# builder = StateGraph(state_schema=MessageGraph)
# builder.add_node(GENERATE, generation_node)
# builder.add_node(TOOLS, tool_node)
# builder.add_node(REFLECT, reflection_node)
# builder.set_entry_point(GENERATE)
#
# def _should_continue(state: MessageGraph) -> str:
#         if getattr(state["messages"][LAST], "tool_calls", None):
#             return TOOLS
#         if len(state["messages"]) > 6:
#             return END
#         return REFLECT
#
# builder.add_conditional_edges(GENERATE, _should_continue, path_map={TOOLS: TOOLS, REFLECT: REFLECT, END: END})
# builder.add_edge(TOOLS, GENERATE)
# builder.add_edge(REFLECT, GENERATE)
#
# graph = builder.compile()
# print(graph.get_graph().draw_mermaid())

# class LanggraphAgent:
#     def __init__(self):
#         self.AGENT_REASON = "agent_reason"
#         self.ACT = "act"
#         self.LAST = -1
#         self.tool_node = tool_node
#         self.app = self.build()
#
#
#
#     def build(self):
#
#         flow = StateGraph(MessagesState) # type: ignore[arg-type]
#
#         flow.add_node(self.AGENT_REASON, run_agent_reasoning) # type: ignore[arg-type]
#         flow.set_entry_point(self.AGENT_REASON)
#         flow.add_node(self.ACT, self.tool_node)
#
#         flow.add_conditional_edges(self.AGENT_REASON, self._should_continue, {
#             END:END,
#             self.ACT:self.ACT})
#
#         flow.add_edge(self.ACT, self.AGENT_REASON)
#
#         app = flow.compile()
#         app.get_graph().draw_mermaid_png(output_file_path="graph.png")
#         return app

if __name__ == "__main__":
    print("Welcome to LangGraph!")
    res = graph.invoke({
        "messages": [
            {
                "role": "user",
                "content": "Give me a relationship between brand shares and market sizes."
            }
        ]
    })
    last_message = res["messages"][LAST]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        print(last_message.tool_calls[0]["args"]["answer"])
    print(res)
