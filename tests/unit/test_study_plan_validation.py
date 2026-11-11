from smart_study_planner.validation import (
    missing_requirement_labels,
    validate_study_plan_data,
)

REQUIREMENTS = {
    "subject": "Python",
    "days_remaining": 2,
    "current_preparation_level": "Beginner",
    "topics": ["Functions", "Classes"],
    "available_hours_per_day": 3,
}

VALID_PLAN = {
    "subject": "Python",
    "days": [
        {
            "day_number": 1,
            "focus_topics": ["Functions"],
            "learning_hours": 1,
            "practice_hours": 1,
            "revision_hours": 0.5,
            "practice_activities": ["Solve two function exercises"],
            "revision_focus": "Function syntax",
            "is_mock_test_day": False,
        },
        {
            "day_number": 2,
            "focus_topics": ["Classes"],
            "learning_hours": 0.5,
            "practice_hours": 1,
            "revision_hours": 1,
            "practice_activities": ["Complete a mixed mock test"],
            "revision_focus": "Functions and classes",
            "is_mock_test_day": True,
        },
    ],
    "final_exam_preparation": "Review mistakes and rest before the exam.",
}


def test_valid_plan_is_approved():
    report = validate_study_plan_data(REQUIREMENTS, VALID_PLAN)

    assert report == {"status": "approved", "issues": []}


def test_missing_requirements_are_named_without_guessing_values():
    missing = missing_requirement_labels(
        {
            "subject": "Python",
            "days_remaining": None,
            "current_preparation_level": None,
            "topics": [],
            "available_hours_per_day": 3,
        }
    )

    assert missing == [
        "number of preparation days",
        "current preparation level",
        "syllabus topics",
    ]


def test_invalid_plan_reports_all_hard_constraint_failures():
    invalid_plan = {
        "subject": "Java",
        "days": [
            {
                "day_number": 1,
                "focus_topics": ["Functions"],
                "learning_hours": 2,
                "practice_hours": 2,
                "revision_hours": 0,
                "practice_activities": [],
                "revision_focus": "",
                "is_mock_test_day": False,
            }
        ],
        "final_exam_preparation": "",
    }

    report = validate_study_plan_data(REQUIREMENTS, invalid_plan)
    issues = " ".join(report["issues"])

    assert report["status"] == "needs_improvement"
    assert "does not match" in issues
    assert "exactly 2" in issues
    assert "exceeding the 3-hour limit" in issues
    assert "Missing syllabus topics: Classes" in issues
    assert "practice time and specific activities" in issues
    assert "revision session" in issues
    assert "final day must include the mock test" in issues
    assert "Final exam preparation guidance" in issues

