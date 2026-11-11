from google.adk.agents import (
    Agent,
    SequentialAgent,
    ParallelAgent,
    LoopAgent,
)

from google.adk.tools import ToolContext

# Use the model that worked for Task 1.
MODEL = "gemini-3.8-flash"


# Tool used to stop the review loop early.
def exit_review_loop(tool_context: ToolContext) -> dict:
    """Stop the review loop after the study plan is approved."""
    tool_context.actions.escalate = True
    return {"status": "approved", "message": "Review completed"}



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

    Clearly organize the requirements.
    Do not invent missing information.
    Keep the output concise.
    """,
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
    """,
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

    Review the plan against these five criteria:

    1. Are all syllabus topics covered?
    2. Does each day stay within available study hours?
    3. Is sufficient coding practice included?
    4. Is revision included?
    5. Is the final day suitable for exam preparation?

    IF ALL CRITERIA PASS:
    - Call exit_review_loop to approve and stop the loop.
    - Present the COMPLETE 10-day study plan.
    - Include the day, topic, study hours,
      practice activities and revision.
    - Clearly state: APPROVED.

    IF ANY CRITERION FAILS:
    - Do not call exit_review_loop.
    - Clearly list the specific corrections required.
    - State: NEEDS IMPROVEMENT.
    - Include the current complete draft plan
    so it remains visible if the iteration limit is reached.

    The review loop has a maximum of 2 iterations.
    Do not claim the plan is approved if issues remain.
    """,

    tools=[exit_review_loop],
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


root_agent = SequentialAgent(
    name="smart_study_planner",
    description=(
        "An intelligent multi-agent study planning system "
        "using Sequential, Parallel and Loop workflows."
    ),
    sub_agents=[
        coordinator_agent,
        planning_agent,
        parallel_analysis,
        review_loop,
    ],
)
