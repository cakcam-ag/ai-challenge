"""
Day 1: Streamlit Frontend for AI Agent
Simple UI for interacting with the AI agent
"""

import streamlit as st
import requests

st.title("Day 1 — My First AI Agent 🤖")
st.markdown("Ask me anything!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if user_input := st.chat_input("Ask something..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/chat",
                    json={"message": user_input},
                    timeout=30
                )
                response.raise_for_status()
                ai_reply = response.json()["reply"]
                st.markdown(ai_reply)
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Make sure the backend is running on port 8000.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
