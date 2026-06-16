"""
Hugging Face Spaces entry point for MedCoach.
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from dotenv import load_dotenv
load_dotenv()

import time
import streamlit as st

from schemas.case import Difficulty, Specialty, StudentDiagnosis
from agents.case_generator import CaseGenerator
from agents.patient import PatientSimulator
from graph.workflow import graph


def stream_text(text: str, speed: float = 0.02):
    for word in text.split(" "):
        yield word + " "
        time.sleep(speed)


# ── Page config ──
st.set_page_config(
    page_title="MedCoach",
    page_icon="🩺",
    layout="wide",
)

st.markdown("""
<style>
.block-container{max-width:1200px;padding-top:2rem;}
.patient-card{padding:18px;border-radius:14px;background:rgba(120,120,120,.08);border:1px solid rgba(120,120,120,.15);color:inherit;}
.section-title{font-size:18px;font-weight:700;margin-bottom:10px;}
.body-text{font-size:15px;line-height:1.8;word-break:break-word;color:inherit;}
.small-card{padding:16px;border-radius:14px;border:1px solid rgba(120,120,120,.15);background:rgba(120,120,120,.05);text-align:center;}
.metric-title{font-size:13px;opacity:.7;margin-bottom:8px;}
.metric-value{font-size:30px;font-weight:700;white-space:normal;}
</style>
""", unsafe_allow_html=True)

# ── Session state ──
defaults = {"case": None, "messages": [], "conversation": [], "show_diagnosis": False}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Case generation ──
def generate_case(difficulty, specialty):
    case = CaseGenerator().generate(
        Difficulty[difficulty.upper()],
        Specialty[specialty.upper()]
    )
    st.session_state.case = case
    st.session_state.messages = []
    st.session_state.conversation = []
    st.session_state.show_diagnosis = False
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Patient generated.\n\nInterview the patient.\n\nSubmit diagnosis when ready."
    })


# ── Sidebar ──
with st.sidebar:
    st.title("🩺 MedCoach")
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
    specialty = st.selectbox("Specialty", [
        "General", "Cardiology", "Pulmonology", "Neurology", "Gastroenterology"
    ])
    if st.button("Generate Patient", type="primary", use_container_width=True):
        generate_case(difficulty, specialty)
        st.rerun()
    st.divider()
    st.info("1. Generate case\n\n2. Interview patient\n\n3. Submit diagnosis\n\n4. Learn")

# ── Header ──
st.title("🩺 MedCoach")
st.caption("Clinical Reasoning Tutor")

if st.session_state.case is None:
    st.info("Generate a patient.")
    st.stop()

case = st.session_state.case
v = case.vitals

# ── Patient overview ──
with st.container(border=True):
    st.subheader("Patient Overview")
    left, right = st.columns([1, 2])
    with left:
        st.markdown(f"""
        <div class='small-card'>
        <div class='metric-title'>Patient</div>
        <div class='metric-value'>{case.age}{"M" if case.gender.lower()=="male" else "F"}</div>
        </div>
        """, unsafe_allow_html=True)
    with right:
        st.markdown(f"""
        <div class='patient-card'>
        <div class='section-title'>Complaint</div>
        <div class='body-text'>{case.complaint}</div>
        <br>
        <div class='section-title'>History</div>
        <div class='body-text'>{case.history}</div>
        </div>
        """, unsafe_allow_html=True)
    st.divider()
    cols = st.columns(5)
    metrics = [
        ("BP", f"{v.bp_systolic}/{v.bp_diastolic}"),
        ("HR", f"{v.heart_rate} bpm"),
        ("Temp", f"{v.temperature}°C"),
        ("RR", f"{v.respiratory_rate}/min"),
        ("SpO₂", f"{v.oxygen_saturation}%"),
    ]
    for col, (title, value) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class='small-card'>
            <div class='metric-title'>{title}</div>
            <div class='metric-value'>{value}</div>
            </div>
            """, unsafe_allow_html=True)

# ── Chat ──
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Ask the patient...")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    patient = PatientSimulator()
    full_answer = ""
    with st.chat_message("assistant"):
        st.toast("Patient is thinking...", icon="🤔")
        placeholder = st.empty()
        stream = patient.respond_stream(
            prompt, case.model_dump(), st.session_state.conversation
        )
        full_answer = placeholder.write_stream(stream)

    st.session_state.conversation.extend([f"user:{prompt}", f"patient:{full_answer}"])
    st.session_state.messages.append({"role": "assistant", "content": full_answer})
    st.rerun()

# ── Diagnosis ──
st.divider()
if st.button("🧠 Submit Diagnosis", use_container_width=True):
    st.session_state.show_diagnosis = True

if st.session_state.show_diagnosis:
    with st.form("diagnosis_form"):
        diagnosis = st.text_input("Diagnosis")
        reasoning = st.text_area("Clinical reasoning")
        evaluate = st.form_submit_button("Evaluate")

    if evaluate:
        with st.spinner("🔍 Analyzing your clinical reasoning..."):
            result = graph.invoke({
                "case": case,
                "conversation": st.session_state.conversation,
                "student_answer": StudentDiagnosis(diagnosis=diagnosis, reasoning=reasoning),
                "evaluation": None,
                "teaching": None,
                "next_action": "evaluate_diagnosis",
            })

        evaluation = result["evaluation"]
        teaching = result.get("teaching")

        st.success(f"**Score: {evaluation.score}/10**")
        if evaluation.strengths:
            st.markdown("**✅ What you did well:**")
            for s in evaluation.strengths:
                st.markdown(f"- {s}")
        if evaluation.missed_items:
            st.markdown("**❌ What you missed:**")
            for m in evaluation.missed_items:
                st.markdown(f"- {m}")
        if evaluation.biases:
            st.markdown("**⚠️ Reasoning biases:**")
            for b in evaluation.biases:
                st.markdown(f"- {b}")
        if evaluation.dangerous_assumptions:
            st.markdown("**🚨 Dangerous assumptions:**")
            for d in evaluation.dangerous_assumptions:
                st.markdown(f"- {d}")
        if evaluation.suggestions:
            st.markdown("**💡 Suggestions:**")
            for s in evaluation.suggestions:
                st.markdown(f"- {s}")
        st.markdown("---")
        st.markdown(f"**Feedback:** {evaluation.overall_feedback}")

        if teaching:
            st.divider()
            st.subheader("📚 Teaching")
            st.markdown("**Explanation:**")
            st.write_stream(stream_text(teaching.explanation))
            st.info(f"**Missed Concept:** {teaching.missed_concept}")
            st.success(f"**Better Approach:** {teaching.better_approach}")
            if teaching.key_takeaways:
                st.markdown("**🎯 Key Takeaways:**")
                for t in teaching.key_takeaways:
                    st.markdown(f"- {t}")
            if teaching.resources:
                st.markdown("**📖 Study Resources:**")
                for r in teaching.resources:
                    st.markdown(f"- {r}")

        st.session_state.show_diagnosis = False
