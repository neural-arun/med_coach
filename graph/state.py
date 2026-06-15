"""
graph/state.py

Defines the shared State object that LangGraph passes between nodes.
Every agent reads from and writes to this state as the workflow progresses.
"""

from typing import TypedDict, Annotated, Optional
from schemas.case import PatientCase, StudentDiagnosis, EvaluationResult, TeachingFeedback


def retain_history(a: list[str], b: list[str]) -> list[str]:
    """
    Merge function for conversation history.
    LangGraph calls this when multiple updates target the same key.
    Simply extends the list with new messages.
    """
    return a + b


class AgentState(TypedDict):
    """
    Shared state flowing through the LangGraph workflow.

    Fields evolve as the student progresses through the tutoring session.
    """
    case: Optional[PatientCase]
    conversation: Annotated[list[str], retain_history]
    student_answer: Optional[StudentDiagnosis]
    evaluation: Optional[EvaluationResult]
    teaching: Optional[TeachingFeedback]
    next_action: str
