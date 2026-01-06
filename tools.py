from langchain_community.tools import WikipediaQueryRun , DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import Tool
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class ResearchResponse(BaseModel):
    topic: str
    summary: str
    sources: list[str]
    tools_used: list[str]

def save_to_text(data:str,filename:str = "research_output.txt"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"--- Research Output --- \nTimestamp: {timestamp}\n\n{data}\n\n"

    with open(filename,"a",encoding="utf-8") as f:
        f.write(formatted_text)
    return f"data successfully saved to {filename}"

save_tool = Tool(
    name="save_text_to_file",
    func=save_to_text,
    description= "Saves structured reasearch data to a text file.",
)

# search = DuckDuckGoSearchRun()
# search_tool = Tool(
#     name="search",
#     func=search.run,
#     description= "Search the web for information",

# )

api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=100)
wiki_tool = WikipediaQueryRun(api_wrapper=api_wrapper)

def run_agent(query: str):
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    parser = PydanticOutputParser(pydantic_object=ResearchResponse)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a research assistant that will help generate a research paper.
                Answer the user query and use neccessary tools.
                Wrap the output in this format and provide no other text\n{format_instructions}
                """,
            ),
            ("placeholder" , "{chat_history}"),
            ("human", "{query}"),
            ("placeholder","{agent_scratchpad}"),
        ]

    ).partial(format_instructions=parser.get_format_instructions())


    tools = [wiki_tool,save_tool]
    agent = create_tool_calling_agent(
        llm=llm,
        prompt=prompt,
        tools= tools
    )

    agent_executor = AgentExecutor(agent=agent,tools=tools,verbose=True)
    raw_response = agent_executor.invoke({"query": query})
    
    try:
        structured_response = parser.parse(raw_response.get("output"))
        return structured_response
    except Exception as e:
        # Fallback if parsing fails, or return raw output
        print("Error parsing response", e, "Raw Response - ", raw_response)
        return raw_response.get("output")
