"""
agents/teacher.py

Provides structured teaching feedback after the evaluator scores the student.
Explains the disease, highlights what the student missed, and teaches
a better clinical reasoning approach — without simply giving the answer.
"""

import json
import os
from openai import OpenAI
from schemas.case import TeachingFeedback


class Teacher:
    """
    Generates educational feedback tailored to the student's performance.

    Usage:
        teacher = Teacher()
        feedback = teacher.teach(evaluation_dict, case_dict)
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

    def _build_prompt(self, evaluation_dict: dict, case_dict: dict) -> str:
        return (
            "You are an experienced medical tutor teaching a student after a clinical reasoning exercise.\n\n"
            f"Case (including actual diagnosis):\n{json.dumps(case_dict, indent=2)}\n\n"
            f"Evaluation of the student:\n{json.dumps(evaluation_dict, indent=2)}\n\n"
            "Provide detailed teaching feedback. Return ONLY valid JSON:\n"
            "- explanation: string (detailed explanation — pathophysiology, presentation, key features, red flags)\n"
            "- missed_concept: string (what they missed, why it matters, how to approach it next time)\n"
            "- better_approach: string (step-by-step systematic approach for similar cases)\n"
            "- key_takeaways: list of strings (3-5 concise learning points)\n"
            "- resources: list of strings (specific topics to study)\n\n"
            "Rules: Teach HOW to think, not WHAT to think. Be encouraging but direct.\n\n"
            "Only JSON. No extra text."
        )

    def teach(self, evaluation_dict: dict, case_dict: dict) -> TeachingFeedback:
        prompt = self._build_prompt(evaluation_dict, case_dict)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
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
        return TeachingFeedback(**data)

    def teach_stream(
        self,
        evaluation_dict: dict,
        case_dict: dict,
    ):
        """
        Streaming version — yields raw text chunks.
        """
        prompt = self._build_prompt(evaluation_dict, case_dict)
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta
