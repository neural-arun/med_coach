# graph/

Purpose:
Controls system flow.

Rule:
Agents do work.
Graph decides order.

Files:

workflow.py
What happens:
- Connects nodes
- Defines execution path
- Decides next step

Flow:

START
 ↓
Case Generator
 ↓
Patient
 ↓
Evaluator
 ↓
Teacher
 ↓
END


state.py
What happens:
- Stores application state
- Shares data between agents

Example State:

{
 case,
 messages,
 student_answer,
 evaluation
}
