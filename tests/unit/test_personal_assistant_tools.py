from personal_assistant.agent import root_agent
from personal_assistant.tools import calculator, text_analyzer


def test_calculator_returns_exact_result():
    assert calculator("25000 * 18 / 100") == {
        "status": "success",
        "expression": "25000 * 18 / 100",
        "result": 4500.0,
    }


def test_calculator_rejects_unsupported_code():
    result = calculator("__import__('os').getcwd()")

    assert result["status"] == "error"


def test_text_analyzer_counts_exact_text():
    assert text_analyzer("Study steadily. Rest well!") == {
        "status": "success",
        "characters": 26,
        "words": 4,
        "sentences": 2,
    }


def test_student_companion_contains_both_specialists():
    assert [agent.name for agent in root_agent.sub_agents] == [
        "intent_router",
        "smart_study_planner",
        "personal_ai_assistant",
    ]
