"""
Day 3: Streamlit Frontend for Interactive Spec Gathering

Natural-language conversation:
- The agent asks up to two clarification questions.
- Then it returns a final spec and stops asking questions.

This UI adds a nicer layout with sidebar instructions and
highlighted final spec.
"""

import streamlit as st
import requests

st.set_page_config(
    page_title="Day 3 — Spec Agent",
    page_icon="📝",
    layout="wide",
)

BACKEND_URL = "http://127.0.0.1:8000/chat"

# Sidebar with instructions
with st.sidebar:
    st.header("Day 3 – Interaction")
    st.markdown(
        """
**How it works**
- Step 1: Describe a feature or idea.
- Step 2: Answer up to a couple of follow‑up questions.
- Step 3: The agent will stop and output a final spec.

**Tips**
- Be concrete about inputs/outputs.
- Mention constraints (platform, latency, etc.) if relevant.
"""
    )

st.markdown(
    "<h2 style='margin-bottom:0.5rem;'>Interactive Spec Agent 🤖</h2>"
    "<p style='color:gray;margin-top:0;'>Describe a feature or product. The agent will ask a few questions and then return a final technical spec.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# State: messages + whether spec is finalized
if "messages" not in st.session_state:
    st.session_state.messages = []
if "spec_finalized" not in st.session_state:
    st.session_state.spec_finalized = False
if "question_index" not in st.session_state:
    st.session_state.question_index = 0
if "initialized" not in st.session_state:
    st.session_state.initialized = False

# Simple 5-step template for progress tracker
STEPS = [
    "Project name and purpose",
    "Target users / audience",
    "Key features and functionality",
    "Technical requirements",
    "Success criteria / metrics",
]


def add_message(role: str, content: str):
    st.session_state.messages.append({"role": role, "content": content})


# On first load, auto-init conversation so the assistant asks the first question
if not st.session_state.initialized:
    try:
        resp = requests.post(
            BACKEND_URL,
            json={"message": "INIT_CONVERSATION"},
            timeout=5,
        )
        resp.raise_for_status()
        ai_reply = resp.json().get("reply", "")
        add_message("assistant", ai_reply)

        # First question should increment progress
        if isinstance(ai_reply, str) and ai_reply.strip().startswith("QUESTION:") and (
            st.session_state.question_index < len(STEPS)
        ):
            st.session_state.question_index += 1
    except Exception:
        # Fail silently; user will still be able to type
        pass
    st.session_state.initialized = True


# Chat input MUST be at the top-level (Streamlit limitation)
input_prompt = (
    "Describe your feature or answer the agent's question..."
    if not st.session_state.spec_finalized
    else "Final spec generated. Refresh the page to start a new session."
)
user_input = st.chat_input(input_prompt, disabled=st.session_state.spec_finalized)


chat_col, spec_col = st.columns([2, 1])

with chat_col:
    st.subheader("Conversation")

    # Render chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle new user input
    if user_input and not st.session_state.spec_finalized:
        add_message("user", user_input)

        with st.chat_message("user"):
            st.markdown(user_input)

        # Call backend with full history so the model can continue the sequence
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    resp = requests.post(
                        BACKEND_URL,
                        json={"message": user_input, "history": st.session_state.messages},
                        timeout=60,
                    )
                    resp.raise_for_status()
                    ai_reply = resp.json().get("reply", "")

                    st.markdown(ai_reply)
                    add_message("assistant", ai_reply)

                    # Detect question vs final spec by markers
                    if isinstance(ai_reply, str):
                        text = ai_reply.strip()
                        if text.startswith("QUESTION:") and st.session_state.question_index < len(STEPS):
                            st.session_state.question_index += 1
                        if text.startswith("FINAL_SPEC:"):
                            st.session_state.spec_finalized = True
                            st.session_state.question_index = len(STEPS)
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend. Make sure the Day 3 backend is running on port 8000.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

with spec_col:
    st.subheader("Progress & Final Spec")

    # Progress tracker
    completed = st.session_state.question_index
    total = len(STEPS)
    st.markdown("**Progress**")
    st.progress(completed / total if total else 0)
    for idx, step in enumerate(STEPS):
        if completed > idx:
            st.markdown(f"- ✅ **{step}**")
        else:
            st.markdown(f"- ⬜ **{step}**")

    st.markdown("---")

    if st.session_state.spec_finalized:
        # Find the last assistant message that starts with FINAL_SPEC:
        final_spec = None
        for msg in reversed(st.session_state.messages):
            if msg["role"] == "assistant" and isinstance(msg["content"], str) and msg[
                "content"
            ].strip().startswith("FINAL_SPEC:"):
                final_spec = msg["content"].replace("FINAL_SPEC:", "", 1).strip()
                break

        if final_spec:
            st.markdown(
                "<div style='padding:0.75rem 1rem;border-radius:0.5rem;"
                "background-color:#f8f9fb;border:1px solid #e0e0e0;overflow:auto;'>"
                f"{final_spec}"
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.write("Spec not found in conversation history.")
    else:
        st.write("Once the agent generates a final spec, it will appear here.")




