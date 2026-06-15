"""
agents/patient.py

Acts as a simulated patient who answers student questions.
Only responds to what is explicitly asked and never reveals the diagnosis.
Maintains consistency with the case details throughout the conversation.
"""

import json
import os
from openai import OpenAI


class PatientSimulator:
    """
    Simulates a patient who answers clinical questions.

    Usage:
        patient = PatientSimulator()
        reply = patient.respond("Do you smoke?", case, conversation)
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

    def _build_prompt(self, question: str, case_dict: dict, conversation: list[str]) -> str:
        safe_case = {k: v for k, v in case_dict.items() if k != "diagnosis"}
        history_text = "\n".join(conversation[-6:]) if conversation else "No prior conversation."
        return (
            "You are a patient in a hospital. A medical student is asking you questions.\n\n"
            "Rules:\n"
            "- Answer ONLY what is asked. Do not volunteer extra information.\n"
            "- Never reveal your diagnosis — you do not know it.\n"
            "- Stay consistent with the case details below.\n"
            "- Respond naturally, like a real person.\n"
            "- Keep responses brief and conversational.\n\n"
            f"Your case details:\n{json.dumps(safe_case, indent=2)}\n\n"
            f"Conversation so far:\n{history_text}\n\n"
            f"Student: {question}\n"
            "You:"
        )

    def respond(self, question: str, case_dict: dict, conversation: list[str]) -> str:
        """
        Non-streaming: return the full patient response as a string.
        """
        prompt = self._build_prompt(question, case_dict, conversation)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content

    def respond_stream(self, question: str, case_dict: dict, conversation: list[str]):
        """
        Streaming generator: yields text chunks as they arrive from the LLM.
        Use with st.write_stream() in the UI.
        """
        prompt = self._build_prompt(question, case_dict, conversation)
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
