"""
app/main.py

Entry point for the MedCoach application.
Starts a FastAPI server with the Gradio UI mounted at /gradio.
"""

import os
from dotenv import load_dotenv

load_dotenv()

import gradio as gr
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

app = FastAPI(title="MedCoach — Clinical Reasoning Tutor", version="0.1.0")


@app.get("/health")
def health_check():
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/")
def root():
    """Redirect browser to the Gradio UI."""
    return RedirectResponse(url="/gradio")


def main():
    """Mount Gradio UI and start the server."""
    from ui.gradio_ui import create_ui

    ui = create_ui()
    app_final = gr.mount_gradio_app(app, ui, path="/gradio")

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(app_final, host=host, port=port)


if __name__ == "__main__":
    main()
