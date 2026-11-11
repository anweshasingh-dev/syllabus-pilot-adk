from typing import Any

from google.adk.tools import ToolContext
from pydantic import ValidationError

from .schemas import StudentRequirements, StudyPlan

REQUIREMENT_LABELS = {
    "subject": "subject",
    "days_remaining": "number of preparation days",
    "current_preparation_level": "current preparation level",
    "topics": "syllabus topics",
    "available_hours_per_day": "available study hours per day",
}


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def missing_requirement_labels(requirements: dict[str, Any]) -> list[str]:
    """Return human-readable labels for required values that are absent."""
    missing = []
    for field_name, label in REQUIREMENT_LABELS.items():
        value = requirements.get(field_name)
        if value is None or value == "" or value == []:
            missing.append(label)
    return missing


def validate_study_plan_data(
    requirements_data: dict[str, Any], plan_data: dict[str, Any]
) -> dict[str, Any]:
    """Validate exact study-plan constraints without relying on an LLM."""
    try:
        requirements = StudentRequirements.model_validate(requirements_data)
        plan = StudyPlan.model_validate(plan_data)
    except ValidationError as error:
        return {
            "status": "needs_improvement",
            "issues": [f"The structured plan is invalid: {error}"],
        }

    missing = missing_requirement_labels(requirements.model_dump())
    if missing:
        return {
            "status": "needs_improvement",
            "issues": ["Missing student requirements: " + ", ".join(missing)],
        }

    issues: list[str] = []
    expected_days = requirements.days_remaining
    daily_limit = requirements.available_hours_per_day
    expected_topics = {_normalized(topic): topic for topic in requirements.topics}

    if _normalized(plan.subject) != _normalized(requirements.subject):
        issues.append(
            f"Plan subject '{plan.subject}' does not match '{requirements.subject}'."
        )

    if len(plan.days) != expected_days:
        issues.append(
            f"Plan contains {len(plan.days)} days; exactly {expected_days} are required."
        )

    day_numbers = [day.day_number for day in plan.days]
    required_day_numbers = list(range(1, expected_days + 1))
    if sorted(day_numbers) != required_day_numbers:
        issues.append(
            "Day numbers must be unique and cover every day from 1 through "
            f"{expected_days}."
        )

    covered_topics: set[str] = set()
    total_practice_hours = 0.0
    has_practice_activity = False
    has_revision = False

    for day in plan.days:
        total_hours = day.learning_hours + day.practice_hours + day.revision_hours
        if total_hours <= 0:
            issues.append(f"Day {day.day_number} has no study time allocated.")
        if total_hours > daily_limit + 1e-9:
            issues.append(
                f"Day {day.day_number} totals {total_hours:g} hours, exceeding "
                f"the {daily_limit:g}-hour limit."
            )

        covered_topics.update(_normalized(topic) for topic in day.focus_topics)
        total_practice_hours += day.practice_hours
        has_practice_activity = has_practice_activity or bool(day.practice_activities)
        has_revision = has_revision or day.revision_hours > 0

    missing_topics = [
        original
        for normalized, original in expected_topics.items()
        if normalized not in covered_topics
    ]
    if missing_topics:
        issues.append("Missing syllabus topics: " + ", ".join(missing_topics) + ".")

    if total_practice_hours <= 0 or not has_practice_activity:
        issues.append("The plan must include practice time and specific activities.")
    if not has_revision:
        issues.append("The plan must include at least one revision session.")

    if plan.days:
        final_day = max(plan.days, key=lambda day: day.day_number)
        if not final_day.is_mock_test_day:
            issues.append("The final day must include the mock test.")
        if final_day.revision_hours <= 0:
            issues.append("The final day must include revision for exam preparation.")

    if not plan.final_exam_preparation.strip():
        issues.append("Final exam preparation guidance is required.")

    return {
        "status": "approved" if not issues else "needs_improvement",
        "issues": issues,
    }


def validate_study_plan(tool_context: ToolContext) -> dict[str, Any]:
    """Validate the current draft against the original student requirements."""
    requirements = tool_context.state.get("student_requirements", {})
    plan = tool_context.state.get("draft_study_plan", {})
    report = validate_study_plan_data(requirements, plan)
    tool_context.state["validation_report"] = report
    if report["status"] == "approved":
        tool_context.actions.escalate = True
    return report

