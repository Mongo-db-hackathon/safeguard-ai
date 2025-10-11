from langchain_core.prompts import ChatPromptTemplate
from agent_state import AgentState, ChecklistItem
from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_openai import ChatOpenAI
from config import Config
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from pydantic.v1 import BaseModel, Field
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv
load_dotenv()


llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a video analyst that can answer questions on video provided tools that return your the video information for the users question"),
            ("user", "{user_input}")
        ])

# register the vector search index as a tool and pass the user input and get the response
# pass the response to llm as input and get the response
# display the response of llm