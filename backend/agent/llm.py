import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv()

# AzureChatOpenAI — the LangChain wrapper the brief specifies.
# Uses the Chat Completions API under the hood, which is the standard
# LangGraph-compatible interface (supports tool-calling, streaming, etc.)
llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    temperature=0,  # deterministic — important for structured JSON output
)


def call_llm(prompt: str) -> str:
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
    except Exception as e:
        return f"LLM error: {str(e)}"
