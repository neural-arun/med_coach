"""
agents/evaluator.py

The most critical agent. Reviews the student's diagnosis and reasoning,
scores their clinical thinking, and identifies gaps, biases, and dangerous assumptions.
"""

import json
import os
from openai import OpenAI
from schemas.case import EvaluationResult


class Evaluator:
    """
    Evaluates a student's clinical reasoning against a case.

    Usage:
        evaluator = Evaluator()
        result = evaluator.evaluate("MI", "Chest pain + smoking", case_dict)
    """

    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key or api_key == "sk-or-v1-your-key-here":
            raise ValueError(
                "OPENROUTER_API_KEY not set or still placeholder. "
                "Edit the .env file with your actual key."
            )
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://github.com/medcoach",
                "X-Title": "MedCoach",
            },
        )
        self.model = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")

    def _build_prompt(
        self,
        diagnosis: str,
        reasoning: str,
        case_dict: dict,
        conversation: list[str] | None = None,
    ) -> str:
        conv_text = ""
        if conversation:
            conv_text = "\n".join(conversation)

        prompt = (
            "You are a senior clinical examiner evaluating a medical student.\n\n"
            f"Case details (including actual diagnosis for reference):\n{json.dumps(case_dict, indent=2)}\n\n"
        )
        if conv_text:
            prompt += f"Full student-patient interview:\n{conv_text}\n\n"
        prompt += (
            f"Student's final diagnosis: {diagnosis}\n"
            f"Student's reasoning: {reasoning}\n\n"
            "Evaluate the student's **entire clinical process** — the questions they asked, "
            "the history they gathered, the tests they considered, and their final reasoning.\n\n"
            "Return ONLY valid JSON with these fields:\n"
            "- score: integer 0-10 (how good was their overall clinical reasoning)\n"
            "- strengths: list of strings (what the student did well)\n"
            "- missed_items: list of strings (key tests, history questions, or exams they missed)\n"
            "- biases: list of strings (reasoning biases detected)\n"
            "- dangerous_assumptions: list of strings (unsafe assumptions)\n"
            "- suggestions: list of strings (clear actionable suggestions)\n"
            "- overall_feedback: string (2-3 sentence summary)\n\n"
            "No extra text. Only JSON."
        )
        return prompt

    def evaluate(
        self,
        diagnosis: str,
        reasoning: str,
        case_dict: dict,
        conversation: list[str] | None = None,
    ) -> EvaluationResult:
        prompt = self._build_prompt(diagnosis, reasoning, case_dict, conversation)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        raw = (response.choices[0].message.content or "").strip()
        if not raw:
            raise RuntimeError(f"LLM returned empty response. Raw: {response}")
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1] if "\n" in raw else raw
            raw = raw.rsplit("```", 1)[0].strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print(f"[DEBUG] Raw LLM response:\n{raw}")
            raise
        return EvaluationResult(**data)

    def evaluate_stream(
        self,
        diagnosis: str,
        reasoning: str,
        case_dict: dict,
        conversation: list[str] | None = None,
    ):
        """
        Streaming version — yields raw text chunks as they arrive.
        The caller should collect chunks and parse JSON at the end.
        """
        prompt = self._build_prompt(diagnosis, reasoning, case_dict, conversation)
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta
