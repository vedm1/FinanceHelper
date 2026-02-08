from dotenv import load_dotenv
load_dotenv(override=True)

from langsmith import Client
from langchain_core.output_parsers import StrOutputParser
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model_name="claude-sonnet-4-5", temperature=0)

client = Client()

prompt = client.pull_prompt("searchsystemprompt")

generation_chain = prompt | llm | StrOutputParser()



