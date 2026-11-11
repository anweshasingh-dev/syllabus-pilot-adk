
# SMARTSTUDY - WORKFLOW VERIFICATION
# Checks the multi-agent architecture without calling Gemini API.

from smart_study_planner.agent import root_agent


def show_workflow(agent, level=0):
    indent = "    " * level

    # Display agent name and type
    print(f"{indent}{agent.name} ({type(agent).__name__})")

    # Display maximum review-loop iterations
    if hasattr(agent, "max_iterations"):
        if agent.max_iterations is not None:
            print(f"{indent}    Max iterations: {agent.max_iterations}")

    # Recursively display all child agents
    for child in getattr(agent, "sub_agents", []):
        show_workflow(child, level + 1)


print("=" * 55)
print("SMARTSTUDY - MULTI-AGENT WORKFLOW VERIFICATION")
print("=" * 55)

show_workflow(root_agent)

print("=" * 55)
print("Architecture inspection completed successfully.")
