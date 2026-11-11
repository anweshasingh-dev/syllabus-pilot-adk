
from google.adk.agents import Agent
from google.adk.tools import google_search, AgentTool
from .tools import calculator, text_analyzer
MODEL = "gemini-3.8-flash"

search_agent = Agent(
    name="google_search_specialist",
    model=MODEL,
    description="Searches Google for current and external information.",
    instruction=(
        "You are a Google Search specialist. "
        "Search the web when given a search request. "
        "Return relevant facts with source links when available. "
        "Do not invent facts or search results."
    ),
    tools=[google_search]
)

root_agent = Agent(
    name="personal_ai_assistant",
    model=MODEL,

    description=(
        "A personal AI assistant that can search Google, "
        "perform calculations and analyze text."
    ),

    instruction="""
    You are a helpful Personal AI Assistant.

    You have access to three tools:

    1. google_search_specialist:
       Use for recent news, current events and external facts.

    2. calculator:
       Use whenever accurate mathematical calculation is required.
       Convert natural language mathematical requests into
       valid arithmetic expressions before calling the tool.
       Do not calculate mentally when this tool is appropriate.

    3. text_analyzer:
       Use to count characters, words and sentences in text.
       Pass the exact user-supplied text to the tool.

    IMPORTANT RULES:
    - Select the correct tool according to the user's request.
    - Use multiple tools when a request requires them.
    - For requests needing both search and calculation,
      search first, then calculate using the retrieved information.
    - Never invent tool outputs.
    - Explain results clearly and concisely.
    - If a tool fails, explain the error to the user.
    - For ordinary conversation, respond naturally.
    """,

    tools=[
        AgentTool(agent=search_agent),
        calculator,
        text_analyzer
    ]
)
