# agents/

Purpose:
Contains all AI workers (specialized agents).

Rule:
Each file should do ONE job only.

Files:

case_generator.py
What happens:
- Creates patient cases
- Selects difficulty
- Generates symptoms/history
- Hides diagnosis

Input:
{
 difficulty,
 specialty
}

Output:
{
 patient_case
}


patient.py
What happens:
- Acts like patient
- Answers only asked questions
- Maintains consistency

Input:
Student Question

Output:
Patient Response


evaluator.py
What happens:
- Reviews student reasoning
- Scores answer
- Finds missing logic

Input:
Student Diagnosis

Output:
{
 score,
 mistakes,
 feedback
}


teacher.py
What happens:
- Explains concepts
- Corrects reasoning
- Teaches better process

Input:
Evaluation

Output:
Teaching Feedback
