

Build a **Clinical Reasoning Tutor**.

Why:

* Simple enough for first real system
* Valuable in medical education
* Uses LangGraph naturally
* Can later become OSCE / NEET-PG / MBBS training product

# Product

### MedCoach — AI Clinical Reasoning Tutor
We are building an AI Clinical Reasoning Tutor that acts like a patient + teacher + evaluator to help medical students practice diagnosing cases and improve their clinical thinking.

Student enters:

> "Patient: 55M, chest pain"

System teaches reasoning instead of giving answer.

Output:

* asks follow-up questions
* evaluates student thinking
* gives feedback
* tracks progress

---

# V1 Architecture (simple but real)

```text
Frontend (Gradio / Next.js)
          ↓
API (FastAPI)
          ↓
LangGraph Orchestrator
          ↓
──────────────────────────
1. Case Generator
2. Patient Simulator
3. Evaluator
4. Teacher
5. Memory
──────────────────────────
          ↓
Database
```

---

# Components

## 1. Case Generator Agent

Creates realistic cases.

Input:

```text
Difficulty: Easy
Topic: Cardiology
```

Output:

```text
Age: 54
Complaint: Chest pain
Vitals...
History...
```

Prompt:

```text
Generate structured clinical case.
Don't reveal diagnosis.
```

---

## 2. Patient Simulator Agent

Acts as patient.

Student:

> Do you smoke?

AI:

> Yes, 15 years.

Rules:

* only answer asked question
* never reveal diagnosis
* remain consistent

State:

```python
{
 case_data,
 history,
 vitals,
 revealed_info
}
```

---

## 3. Evaluator Agent (MOST IMPORTANT)

Student submits:

```text
Likely MI because...
```

Evaluator checks:

* reasoning quality
* missing tests
* bias
* dangerous assumptions

Output:

```text
Reasoning: 7/10
Missed:
- ECG
- Troponin
```

This is your uploaded Sidekick pattern reused.

---

## 4. Teacher Agent

After evaluation:

```text
Explain:
- disease
- why student missed
- better approach
```

Never directly solve initially.

---

## 5. Memory

Store:

```text
Student
↓
Weak in:
- cardiology
- differential diagnosis
```

Next cases adapt.

---

# LangGraph Flow

This is the graph.

```text
START
 ↓
Case Generator
 ↓
Patient Simulator
 ↓
Student Input
 ↓
Evaluator
 ↓
Teacher
 ↓
Progress Update
 ↓
END
```

---

# Folder Structure

```text
medical_tutor/

app/
 ├── main.py

agents/
 ├── case_generator.py
 ├── patient.py
 ├── evaluator.py
 ├── teacher.py

graph/
 ├── workflow.py
 ├── state.py

schemas/
 ├── case.py

memory/
 ├── student_memory.py

ui/
 ├── gradio_ui.py
```

---

# Data Model

```python
class State:
    case
    conversation
    student_answer
    evaluation
    next_action
```

---

# Tech Stack (keep simple)

| Layer   | Tool           |
| ------- | -------------- |
| UI      | Gradio         |
| Backend | FastAPI        |
| Agent   | LangGraph      |
| Model   | Openrouter  |
| Storage | SQLite         |
| Logs    | LangSmith      |

---
