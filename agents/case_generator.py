"""
agents/case_generator.py

Creates realistic patient cases for students to diagnose.
Uses an LLM via OpenRouter to generate structured clinical data
based on the requested difficulty and specialty.
"""

import json
import os
from openai import OpenAI
from schemas.case import PatientCase, VitalSigns, Difficulty, Specialty


class CaseGenerator:
    """
    Generates a PatientCase by prompting an LLM.

    Usage:
        generator = CaseGenerator()
        case = generator.generate(difficulty=Difficulty.EASY, specialty=Specialty.CARDIOLOGY)
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

    def generate(self, difficulty: Difficulty, specialty: Specialty) -> PatientCase:
        """
        Generate a clinical case for the given difficulty and specialty.

        Args:
            difficulty: Easy, medium, or hard.
            specialty: Cardiology, pulmonology, etc.

        Returns:
            A fully populated PatientCase (diagnosis is internal only).
        """
        prompt = (
            f"You are a clinical case writer. Generate a unique, realistic patient case.\n\n"
            f"Difficulty: {difficulty.value}\n"
            f"Specialty: {specialty.value}\n\n"
            "Requirements for variety:\n"
            "- Pick from a WIDE range of ages (any between 2 and 95)\n"
            "- Use diverse and less common complaints (not just chest pain or headache)\n"
            "- Choose vitals that match the case (abnormal where appropriate)\n"
            "- Include relevant history that affects the clinical picture\n"
            "- Select a diagnosis from many possible options within the specialty\n"
            "- Avoid the most obvious/common presentations — add twists\n\n"
            "Return ONLY valid JSON with these fields:\n"
            "- age (integer 2-95)\n"
            "- gender (string)\n"
            "- complaint (string, the reason the patient came in)\n"
            "- vitals (object with: bp_systolic, bp_diastolic, heart_rate, temperature, respiratory_rate, oxygen_saturation)\n"
            "- history (string, relevant medical history)\n"
            "- diagnosis (string, the actual diagnosis — this is for internal use, never shown to the student)\n\n"
            "No explanation, no markdown, no extra text. Only JSON."
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0,
        )

        raw = (response.choices[0].message.content or "").strip()
        if not raw:
            raise RuntimeError(
                f"LLM returned empty response. Raw response: {response}"
            )

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1] if "\n" in raw else raw
            raw = raw.rsplit("```", 1)[0].strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print(f"[DEBUG] Raw LLM response:\n{raw}")
            raise

        case = PatientCase(
            age=data["age"],
            gender=data["gender"],
            complaint=data["complaint"],
            vitals=VitalSigns(**data["vitals"]),
            history=data["history"],
            specialty=specialty,
            difficulty=difficulty,
            diagnosis=data["diagnosis"],
        )

        return case
