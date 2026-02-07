import os
import sys

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser, JsonOutputToolsParser, PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

load_dotenv(override=True)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from retrieval import search_documents

from .schemas import AnswerQuestion, ReviseAnswer

# tools = [search_documents]

llm = ChatAnthropic(model_name="claude-sonnet-4-5", temperature=0)
parser = JsonOutputToolsParser(return_id=True)
pydantic_parser = PydanticToolsParser(tools=[AnswerQuestion])

actor_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert in the field and tasked with creating the most useful and meaningful content."
            "Generate the best possible content for the user's request."
            "{revisor_instructions}"
            "If the user provides critique, respond with a revised version of your previous attempts."
            "Reflect and critique your answer. Be severe to maximise improvement"
            "Recommend search queries to research information and improve your answer"
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

first_responder = actor_prompt_template.partial(revisor_instructions="") | llm.bind_tools(
    tools=[AnswerQuestion], tool_choice="AnswerQuestion"
)

revise_instructions = """
                        Revise your previous answer using the new information.
                        -You should use the previous critique to add important information to your answer.
                        -You MUST include citations in your revised answer to ensure it can be verified.
                        -Add a "References" section to the bottom of your answer (which does not count towards the word limit if any is provided). In form of:
                            - [1] "documents/example.md"
                            - [2] "documents/example.json"
                        - You should use your previous critique to remove superfluous information from your answer and make sure you stay within the context.
                    """

revisor = (actor_prompt_template.partial(revisor_instructions=revise_instructions)
           | llm.bind_tools(tools=[ReviseAnswer], tool_choice="ReviseAnswer"))

if __name__ == "__main__":
    human_message = HumanMessage(
        content="Give me the relationship between Brand Shares and Market Sizes and explain with a diagram"
    )

    chain = (
            actor_prompt_template
            | llm.bind_tools(tools=[AnswerQuestion], tool_choice="AnswerQuestion")
            | pydantic_parser
    )
    res = chain.invoke(input={"messages": [human_message]})
    print(res)