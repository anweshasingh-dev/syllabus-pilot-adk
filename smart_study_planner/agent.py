
from collections.abc import AsyncGenerator

from google.adk.agents import (
    Agent,
    BaseAgent,
    LoopAgent,
    ParallelAgent,
    SequentialAgent,
)
from google.adk.agents.invocation_context import InvocationContext
from google.adk.apps import App
from google.adk.events import Event
from google.genai import types
from typing_extensions import override

from .schemas import StudentRequirements, StudyPlan
from .validation import missing_requirement_labels, validate_study_plan

# Use the model that worked for Task 1.
MODEL = "gemini-3.8-flash"


# COORDINATOR AGENT

coordinator_agent = Agent(
    name="coordinator_agent",
    model=MODEL,
    description="Extracts student examination requirements.",
    instruction="""
    Extract these details from the user's request:

    1. Subject
    2. Days remaining until exam
    3. Current preparation level
    4. All topics
    5. Available study hours per day

    Extract only details explicitly supplied by the user anywhere in the
    conversation. Do not invent, estimate, or assume missing information.
    Use null for a missing scalar value and an empty list for missing topics.
    """,
    output_schema=StudentRequirements,
    output_key="student_requirements",
)


# PLANNING AGENT

planning_agent = Agent(
    name="planning_agent",
    model=MODEL,
    description="Prepares structured study-planning requirements.",
    instruction="""
    Student details:
    {student_requirements}

    Prepare a structured planning brief.

    Identify:
    - Topics that need preparation
    - Total available study hours
    - Student's current preparation level
    - Need for practice and revision
    - Need for a final mock test

    Do not create the final study plan.
    Prepare information for the three analysis agents.
    """,
    output_key="planning_brief",
)



# TOPIC AGENT

topic_agent = Agent(
    name="topic_agent",
    model=MODEL,
    description="Analyzes topic difficulty and priority.",
    instruction="""
    Planning brief:
    {planning_brief}

    Analyze EVERY topic in the student's syllabus.

    For each topic provide:
    - Priority: High / Medium / Low
    - Difficulty: Easy / Medium / Hard
    - Recommended study focus

    Consider the student's current level.
    Use a clear table.
    """,
    output_key="topic_analysis",
)


# PRACTICE AGENT

practice_agent = Agent(
    name="practice_agent",
    model=MODEL,
    description="Recommends coding practice and mock tests.",
    instruction="""
    Planning brief:
    {planning_brief}

    Create a practical problem-solving strategy.

    Include:
    - Number of coding problems per topic
    - Conceptual questions
    - Mixed practice
    - Mock tests

    Allocate more practice to difficult topics.

    Keep workload realistic within the study hours.
    """,
    output_key="practice_plan",
)


# SCHEDULE AGENT

schedule_agent = Agent(
    name="schedule_agent",
    model=MODEL,
    description="Creates a realistic day-wise study schedule.",
    instruction="""
    Planning brief:
    {planning_brief}

    Prepare a day-wise schedule covering exactly
    the number of preparation days specified.

    For each day include:
    - Main topic
    - Study duration
    - Practice duration
    - Revision duration

    The total time per day must not exceed
    the student's available hours.

    Cover all topics.
    Include revision and a final mock test.
    """,
    output_key="study_schedule",
)


# PARALLEL WORKFLOW.

parallel_analysis = ParallelAgent(
    name="parallel_analysis",
    sub_agents=[
        topic_agent,
        practice_agent,
        schedule_agent,
    ],
)



# STUDY PLAN WRITER

study_plan_writer = Agent(
    name="study_plan_writer",
    model=MODEL,
    description="Combines all analyses into a complete study plan.",
    instruction="""
    Student requirements:
    {student_requirements}

    Topic analysis:
    {topic_analysis}

    Practice recommendations:
    {practice_plan}

    Proposed schedule:
    {study_schedule}

    Previous reviewer feedback, if any:
    {review_feedback?}

    Create or improve a complete personalized study plan.

    The final plan MUST include:
    1. A day-wise timetable
    2. Topics for each day
    3. Hours allocated to learning, practice and revision
    4. Coding problems and practice activities
    5. Revision sessions
    6. A mock test and final exam preparation

    Make sure the daily total does not exceed
    the student's available study hours.

    If reviewer feedback exists, fix every issue raised.

    Preserve every syllabus topic using its exact supplied name in
    focus_topics. Create exactly the requested number of days. The final day
    must include both revision and the mock test.
    """,
    output_schema=StudyPlan,
    output_key="draft_study_plan",
)


# REVIEW AGENT

review_agent = Agent(
    name="review_agent",
    model=MODEL,
    description="Validates the study plan and requests improvements.",

    instruction="""
    Student requirements:
    {student_requirements}

    Draft study plan:
    {draft_study_plan}

    Call validate_study_plan exactly once. This deterministic tool checks the
    requested day count, original subject and topics, daily hour limit,
    practice, revision, and final mock test.

    Use only the tool result for the approval decision:
    - If status is approved, state APPROVED briefly. The tool will stop the
      review loop.
    - If status is needs_improvement, state NEEDS IMPROVEMENT and list every
      returned issue as precise correction feedback for the next draft.

    Do not reproduce the complete plan and never approve a plan yourself.
    """,

    tools=[validate_study_plan],
    output_key="review_feedback",
)



review_loop = LoopAgent(
    name="review_loop",
    sub_agents=[
        study_plan_writer,
        review_agent,
    ],
    max_iterations=2,
)


# FINAL PRESENTER

final_presenter = Agent(
    name="final_presenter",
    model=MODEL,
    description="Presents an approved plan or a clear validation failure.",
    instruction="""
    Student requirements:
    {student_requirements}

    Latest structured study plan:
    {draft_study_plan}

    Deterministic validation report:
    {validation_report?}

    If validation status is approved, present the complete plan in a readable
    day-wise table. Include exact topics, learning hours, practice hours,
    revision hours, practice activities, and the final mock test. State
    APPROVED.

    If validation is missing or needs_improvement, do not present the plan as
    approved. State VALIDATION FAILED and list the remaining issues. Explain
    that the iteration limit was reached and the user should adjust the input
    or retry.
    """,
)


planning_workflow = SequentialAgent(
    name="planning_workflow",
    sub_agents=[
        planning_agent,
        parallel_analysis,
        review_loop,
        final_presenter,
    ],
)


class SmartStudyPlannerAgent(BaseAgent):
    """Run requirement extraction before starting the planning workflow."""

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        coordinator, workflow = self.sub_agents
        requirements = None

        async for event in coordinator.run_async(ctx):
            if "student_requirements" in event.actions.state_delta:
                requirements = event.actions.state_delta["student_requirements"]
            yield event

        if requirements is None:
            requirements = ctx.session.state.get("student_requirements", {})

        missing = missing_requirement_labels(requirements)
        if missing:
            question = (
                "Before I create the study plan, please provide: "
                + ", ".join(missing)
                + "."
            )
            yield Event(
                author=self.name,
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=question)],
                ),
            )
            return

        async for event in workflow.run_async(ctx):
            yield event


root_agent = SmartStudyPlannerAgent(
    name="smart_study_planner",
    description=(
        "An intelligent multi-agent study planning system "
        "using Sequential, Parallel and Loop workflows."
    ),
    sub_agents=[
        coordinator_agent,
        planning_workflow,
    ],
)

app = App(root_agent=root_agent, name="smart_study_planner")
