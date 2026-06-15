"""
ui/gradio_ui.py

Gradio ChatInterface for MedCoach.
Simple, clean, works out of the box.
"""

from dotenv import load_dotenv

load_dotenv()

import gradio as gr
from graph.workflow import graph
from schemas.case import Difficulty, Specialty, StudentDiagnosis
from agents.case_generator import CaseGenerator
from agents.patient import PatientSimulator

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
_session: dict = {
    "case": None,
    "conversation": [],
    "awaiting_diagnosis": False,
}


# ---------------------------------------------------------------------------
# Chat function
# ---------------------------------------------------------------------------
def chat_fn(message: str, history: list):
    """Handle one student message. Called by ChatInterface for each turn."""

    # ── Generate case on very first message ──
    if _session["case"] is None:
        case_gen = CaseGenerator()
        case = case_gen.generate(Difficulty.EASY, Specialty.GENERAL)
        _session["case"] = case
        _session["conversation"] = []

        vitals = case.vitals
        return (
            f"**New Patient**\n\n"
            f"**{case.age}{'M' if case.gender.lower() == 'male' else 'F'} | {case.complaint}**\n"
            f"BP {vitals.bp_systolic}/{vitals.bp_diastolic} | "
            f"HR {vitals.heart_rate} | "
            f"Temp {vitals.temperature}°C | "
            f"RR {vitals.respiratory_rate} | "
            f"SpO₂ {vitals.oxygen_saturation}%\n\n"
            f"Ask questions to gather more information. "
            f"Type `/diagnosis` when ready to submit your answer."
        )

    # ── /diagnosis — prompt for structured input ──
    if message.strip().lower().startswith("/diagnosis"):
        _session["awaiting_diagnosis"] = True
        return (
            "Submit your **diagnosis** and **reasoning** on separate lines:\n\n"
            "`Diagnosis: <your diagnosis>`\n"
            "`Reasoning: <your reasoning>`"
        )

    # ── Parse diagnosis ──
    if _session["awaiting_diagnosis"]:
        lines = message.strip().split("\n")
        diagnosis_text = ""
        reasoning_text = ""
        for line in lines:
            if line.lower().startswith("diagnosis:"):
                diagnosis_text = line.split(":", 1)[1].strip()
            elif line.lower().startswith("reasoning:"):
                reasoning_text = line.split(":", 1)[1].strip()

        if not diagnosis_text:
            return (
                "Could not parse. Use:\n"
                "`Diagnosis: <your diagnosis>`\n"
                "`Reasoning: <your reasoning>`"
            )

        _session["awaiting_diagnosis"] = False

        state = {
            "case": _session["case"],
            "conversation": list(_session["conversation"]),
            "student_answer": StudentDiagnosis(
                diagnosis=diagnosis_text,
                reasoning=reasoning_text or "No reasoning provided.",
            ),
            "evaluation": None,
            "teaching": None,
            "next_action": "evaluate_diagnosis",
        }

        result = graph.invoke(state)
        evaluation = result.get("evaluation")
        teaching = result.get("teaching")

        lines = [f"## Evaluation", f"**Score:** {evaluation.score}/10"]
        if evaluation.missed_items:
            lines.append(f"\n**Missed:** {', '.join(evaluation.missed_items)}")
        if evaluation.biases:
            lines.append(f"\n**Biases:** {', '.join(evaluation.biases)}")
        if evaluation.dangerous_assumptions:
            lines.append(
                f"\n**Dangerous:** {', '.join(evaluation.dangerous_assumptions)}"
            )
        lines.append(f"\n**Feedback:** {evaluation.overall_feedback}")

        if teaching:
            lines.extend([
                "\n---\n## Teaching",
                f"\n**Explanation:** {teaching.explanation}",
                f"\n**Missed Concept:** {teaching.missed_concept}",
                f"\n**Better Approach:** {teaching.better_approach}",
            ])

        _session["case"] = None
        _session["conversation"] = []

        lines.append("\n---\nStart a new message for a new patient.")
        return "\n".join(lines)

    # ── Normal question → patient answer ──
    case_dict = _session["case"].model_dump()
    conversation = _session["conversation"]

    patient = PatientSimulator()
    reply = patient.respond(message, case_dict, conversation)

    conversation.append(f"student: {message}")
    conversation.append(f"patient: {reply}")

    return reply


# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ui = gr.ChatInterface(
        fn=chat_fn,
        title="🩺 MedCoach — Clinical Reasoning Tutor",
        description=(
            "Practice diagnosing virtual patients. "
            "Ask questions, gather history, then type `/diagnosis` when ready."
        ),
        examples=[
            "Tell me about your chest pain.",
            "Do you have any other symptoms?",
            "/diagnosis",
        ],
        theme=gr.themes.Soft(),
    )
    ui.launch(server_port=7860)
