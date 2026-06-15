"""
schemas/case.py

Defines all Pydantic data structures used throughout MedCoach.
Every agent, graph node, and storage layer relies on these schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Specialty(str, Enum):
    CARDIOLOGY = "cardiology"
    PULMONOLOGY = "pulmonology"
    NEUROLOGY = "neurology"
    GASTROENTEROLOGY = "gastroenterology"
    GENERAL = "general"


class VitalSigns(BaseModel):
    bp_systolic: int = Field(..., description="Systolic blood pressure in mmHg")
    bp_diastolic: int = Field(..., description="Diastolic blood pressure in mmHg")
    heart_rate: int = Field(..., description="Heart rate in bpm")
    temperature: float = Field(..., description="Body temperature in Celsius")
    respiratory_rate: int = Field(..., description="Respirations per minute")
    oxygen_saturation: int = Field(..., description="SpO2 percentage")


class PatientCase(BaseModel):
    age: int = Field(..., ge=0, le=120, description="Patient age in years")
    gender: str = Field(..., description="Patient gender")
    complaint: str = Field(..., description="Primary complaint")
    vitals: VitalSigns
    history: str = Field(..., description="Relevant medical history")
    specialty: Specialty
    difficulty: Difficulty
    diagnosis: Optional[str] = Field(None, description="Actual diagnosis (hidden from student)")


class StudentDiagnosis(BaseModel):
    diagnosis: str = Field(..., description="Student's final diagnosis")
    reasoning: str = Field(..., description="Student's reasoning process")
    differentials: list[str] = Field(default_factory=list, description="Differential diagnoses considered")


class EvaluationResult(BaseModel):
    score: int = Field(..., ge=0, le=10, description="Reasoning score out of 10")
    strengths: list[str] = Field(default_factory=list, description="What the student did well")
    missed_items: list[str] = Field(default_factory=list, description="Missing tests or considerations")
    biases: list[str] = Field(default_factory=list, description="Reasoning biases detected")
    dangerous_assumptions: list[str] = Field(default_factory=list, description="Unsafe assumptions made")
    suggestions: list[str] = Field(default_factory=list, description="Clear actionable suggestions for improvement")
    overall_feedback: str = Field(..., description="Summary evaluation feedback")


class TeachingFeedback(BaseModel):
    explanation: str = Field(..., description="Disease explanation with pathophysiology and clinical features")
    missed_concept: str = Field(..., description="What the student missed, why it matters, and how to approach it next time")
    better_approach: str = Field(..., description="Step-by-step better clinical reasoning approach for similar cases")
    key_takeaways: list[str] = Field(default_factory=list, description="3-5 key learning points the student should remember")
    resources: list[str] = Field(default_factory=list, description="Suggested topics or areas to study further")
