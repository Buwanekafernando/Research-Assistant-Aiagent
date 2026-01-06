import os
from datetime import datetime
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor

load_dotenv()

# 1. Define Output Schema
class ResearchResponse(BaseModel):
    topic: str = Field(description="The main topic of research")
    summary: str = Field(description="A detailed summary of findings")
    sources: list[str] = Field(description="List of sources used")
    tools_used: list[str] = Field(description="Names of tools used during research")

# 2. Define Tools
def save_to_text(data: str, filename: str = "research_output.txt"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"--- Research Output --- \nTimestamp: {timestamp}\n\n{data}\n\n"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(formatted_text)
    return f"Successfully saved to {filename}"

save_tool = Tool(
    name="save_text_to_file",
    func=save_to_text,
    description="Saves final research findings to a text file. Use this ONLY after research is complete.",
)

api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=500)
wiki_tool = WikipediaQueryRun(api_wrapper=api_wrapper)
tools = [wiki_tool, save_tool]

# 3. Agent Setup
def run_agent(query: str):
    # Use Gemini Pro (ensure GOOGLE_API_KEY is in .env)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0)
    
    # In 2026, tool-calling agents work best with specific message placeholders
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a research assistant. Use tools to find info, save it, and then provide a final structured summary."),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Initialize Agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # 4. Execute and Manually Structure (or use with_structured_output)
    raw_response = agent_executor.invoke({"input": query})
    output_text = raw_response.get("output")
    
    # Force structuring of the final string output
    structured_llm = llm.with_structured_output(ResearchResponse)
    return structured_llm.invoke(f"Extract research details from this text: {output_text}")

if __name__ == "__main__":
    result = run_agent("Research the history of the James Webb Space Telescope and save the findings.")
    print("\n--- Structured Result ---")
    print(result.model_dump_json(indent=2))
