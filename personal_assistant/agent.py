from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from google.adk.agents import Agent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.apps import App
from google.adk.events import Event
from google.adk.tools import AgentTool, google_search
from pydantic import BaseModel, Field
from typing_extensions import override

from smart_study_planner.agent import root_agent as study_planner_agent

from .tools import calculator, text_analyzer

load_dotenv(Path(__file__).with_name(".env"))

MODEL = "gemini-3.8-flash"


class RouteDecision(BaseModel):
    """Select the specialist that should handle the user's current request."""

    destination: Literal["study_planner", "personal_assistant"]
    reason: str = Field(description="Brief explanation of the routing choice.")


intent_router = Agent(
    name="intent_router",
    model=MODEL,
    description="Routes requests to study planning or general assistant capabilities.",
    instruction="""
    Route the user's current request using the full conversation context.

    Choose study_planner when the user:
    - asks to create, revise, continue, or explain a study plan or exam timetable;
    - supplies exam-planning requirements such as subject, days, topics, level,
      or available study hours;
    - answers a follow-up question from an unfinished study-planning request.

    Choose personal_assistant for:
    - current information or web research;
    - arithmetic and calculations;
    - word, sentence, or character counts;
    - general conversation and all other requests.

    Route only. Do not answer the user's request.
    """,
    output_schema=RouteDecision,
    output_key="route_decision",
)

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
    tools=[google_search],
)

assistant_agent = Agent(
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
        text_analyzer,
    ],
)


class StudentCompanionAgent(BaseAgent):
    """Route each request to the study planner or personal assistant."""

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        router, planner, assistant = self.sub_agents
        decision = None

        # The routing response is internal; only the selected specialist's
        # events are shown to the user.
        async for event in router.run_async(ctx):
            route_data = event.actions.state_delta.get("route_decision")
            if route_data is not None:
                decision = RouteDecision.model_validate(route_data)

        selected_agent = (
            planner
            if decision is not None and decision.destination == "study_planner"
            else assistant
        )

        async for event in selected_agent.run_async(ctx):
            yield event


root_agent = StudentCompanionAgent(
    name="personal_assistant",
    description=(
        "A student companion that routes study planning, web research, "
        "calculations, text analysis, and general questions."
    ),
    sub_agents=[
        intent_router,
        study_planner_agent,
        assistant_agent,
    ],
)

app = App(root_agent=root_agent, name="personal_assistant")
