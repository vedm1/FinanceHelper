import os
import sys

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

load_dotenv(override=True)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from retrieval import search_documents

tools = [search_documents]

reflection_prompt = ChatPromptTemplate.from_messages(
    [
        (
        "system",
        "You are a reviewer responsible for evaluating whether a given response or document adequately addresses a specific question. You will receive both a QUESTION and an ANSWER (or DOCUMENT). Your assessment should verify if the content incorporates the necessary keywords or semantic meaning required to resolve the inquiry. The evaluation is binary: assign a ‘yes’ if the answer or document fully meets the criteria, or a ‘no’ if it does not."
        "When making your judgment, provide a step-by-step explanation that details your reasoning process. This explanation should outline how the response addresses each aspect of the question, ensuring your conclusion is both transparent and well-supported."
        "The purpose of this task is to filter out irrelevant or erroneous responses rather than to apply an overly strict grading standard."
        ),
        MessagesPlaceholder(variable_name="messages")
    ]
)

generation_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert in the field and tasked with creating the most useful and meaningful content."
            "Generate the best possible content for the user's request."
            "If the user provides critique, respond with a revised version of your previous attempts."
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
        ),
        MessagesPlaceholder(variable_name="messages")
    ]
)

# llm = ChatAnthropic(model_name="claude-sonnet-4-5", temperature=0)
llm_with_tools = ChatAnthropic(model_name="claude-sonnet-4-5", temperature=0).bind_tools(tools)
generate_chain = generation_prompt | llm_with_tools
reflect_chain = reflection_prompt | llm_with_tools