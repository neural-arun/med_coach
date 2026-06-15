"""
graph/workflow.py

Defines the LangGraph StateGraph that orchestrates the MedCoach evaluation pipeline.

This graph runs AFTER the student submits a diagnosis. The interactive parts
(case generation and patient Q&A) are handled directly by the UI since
they require a real-time back-and-forth loop.

Nodes:
    1. evaluate_diagnosis — scores the student's clinical reasoning
    2. teach_student      — provides structured teaching feedback
    3. update_memory      — persists performance data to SQLite

Flow:
    START -> evaluate_diagnosis -> teach_student -> update_memory -> END
"""

from langgraph.graph import StateGraph, START, END
from graph.state import AgentState
from agents.evaluator import Evaluator
from agents.teacher import Teacher
from memory.student_memory import StudentMemory

# ---------------------------------------------------------------------------
# Instantiate agents (singletons — reused across invocations)
# ---------------------------------------------------------------------------
evaluator = Evaluator()
teacher = Teacher()
memory = StudentMemory()


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------
def evaluate_diagnosis_node(state: AgentState) -> dict:
    """
    Run the evaluator on the student's submitted diagnosis and reasoning.
    """
    case_dict = state["case"].model_dump() if state.get("case") else {}
    student_answer = state.get("student_answer")

    if not student_answer:
        return {"evaluation": None, "next_action": "complete"}

    result = evaluator.evaluate(
        diagnosis=student_answer.diagnosis,
        reasoning=student_answer.reasoning,
        case_dict=case_dict,
        conversation=state.get("conversation"),
    )

    return {"evaluation": result, "next_action": "teach"}


def teach_student_node(state: AgentState) -> dict:
    """
    Generate teaching feedback based on the evaluation.
    """
    case_dict = state["case"].model_dump() if state.get("case") else {}
    evaluation_dict = state["evaluation"].model_dump() if state.get("evaluation") else {}

    feedback = teacher.teach(evaluation_dict, case_dict)

    return {"teaching": feedback, "next_action": "complete"}


def update_memory_node(state: AgentState) -> dict:
    """
    Persist student performance data to SQLite.
    """
    case = state.get("case")
    evaluation = state.get("evaluation")

    if case and evaluation:
        memory.save_case(
            specialty=case.specialty.value,
            difficulty=case.difficulty.value,
            score=evaluation.score,
            diagnosis=case.diagnosis or "",
            feedback=evaluation.model_dump(),
        )

    return {"next_action": "done"}


# ---------------------------------------------------------------------------
# Build and compile the graph
# ---------------------------------------------------------------------------
def build_graph() -> StateGraph:
    """
    Construct the evaluation pipeline graph.
    """
    builder = StateGraph(AgentState)

    builder.add_node("evaluate_diagnosis", evaluate_diagnosis_node)
    builder.add_node("teach_student", teach_student_node)
    builder.add_node("update_memory", update_memory_node)

    builder.add_edge(START, "evaluate_diagnosis")
    builder.add_edge("evaluate_diagnosis", "teach_student")
    builder.add_edge("teach_student", "update_memory")
    builder.add_edge("update_memory", END)

    return builder.compile()


# Convenience instance
graph = build_graph()
