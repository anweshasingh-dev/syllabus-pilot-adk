from pydantic import BaseModel, Field


class StudentRequirements(BaseModel):
    """Student details extracted from the conversation."""

    subject: str | None = None
    days_remaining: int | None = Field(default=None, ge=1)
    current_preparation_level: str | None = None
    topics: list[str] = Field(default_factory=list)
    available_hours_per_day: float | None = Field(default=None, ge=0.1)


class DayPlan(BaseModel):
    """One day in a generated study plan."""

    day_number: int = Field(ge=1)
    focus_topics: list[str] = Field(min_length=1)
    learning_hours: float = Field(ge=0)
    practice_hours: float = Field(ge=0)
    revision_hours: float = Field(ge=0)
    practice_activities: list[str] = Field(default_factory=list)
    revision_focus: str = ""
    is_mock_test_day: bool = False


class StudyPlan(BaseModel):
    """Structured study plan that can be validated deterministically."""

    subject: str
    days: list[DayPlan] = Field(min_length=1)
    final_exam_preparation: str

