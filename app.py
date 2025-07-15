# app.py
# The Streamlit UI. This now imports the agent from the 'visceral' package.
# ADDED: A try/except block to catch initialization errors and display them.

import streamlit as st
from visceral.core.agent import VisceralAgent

st.set_page_config(page_title="Visceral AI", page_icon="🧠", layout="wide")

# --- State Management & Error Catching ---
# Wrap the agent initialization in a try/except block to display errors on the page
if 'agent' not in st.session_state:
    try:
        # This is where the app is likely failing.
        st.session_state.agent = VisceralAgent()
        print("INFO: Initialized a new VisceralAgent for the Streamlit session.")
        st.session_state.error = None
    except Exception as e:
        # If it fails, store the error to display it in the UI.
        st.session_state.agent = None
        st.session_state.error = e

if 'messages' not in st.session_state: st.session_state.messages = []
if 'last_decision_id' not in st.session_state: st.session_state.last_decision_id = None
if 'correction_mode' not in st.session_state: st.session_state.correction_mode = False

# --- UI Rendering ---
st.title("🧠 Visceral: The Self-Correcting AI")

# --- Display Initialization Error if it occurred ---
if st.session_state.error:
    st.error("Fatal Error during Agent Initialization:")
    st.code(st.session_state.error)
    st.warning("The application cannot start. Please check the terminal logs and ensure Ollama is running.")
    st.stop() # Stop the script here if the agent failed to load

st.caption("An agent that evolves its logic from your feedback. Start a conversation and help it learn.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "explanation" in message:
            with st.expander("Show Reasoning"):
                st.code(message["explanation"], language="text")

# --- Main Interaction Loop ---
if prompt := st.chat_input("What's on your mind?"):
    st.session_state.last_decision_id = None
    st.session_state.correction_mode = False
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    agent = st.session_state.agent
    with st.spinner("Thinking..."):
        decision = agent.process_query(prompt)
    
    st.session_state.last_decision_id = decision.id
    explanation = agent.explain_decision(decision.id)
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": decision.output,
        "explanation": explanation
    })
    st.rerun()

# --- Feedback & Correction ---
if st.session_state.last_decision_id and not st.session_state.correction_mode:
    st.write("---")
    st.write("**Was this response helpful?**")
    col1, col2, _ = st.columns([1, 1, 5])
    if col1.button("👍 Good", key=f"good_{st.session_state.last_decision_id}"):
        st.session_state.agent.provide_feedback(st.session_state.last_decision_id, rating=5)
        st.toast("Thanks! I'll reinforce this logic.", icon="✅")
        st.session_state.last_decision_id = None
        st.rerun()
    if col2.button("👎 Bad", key=f"bad_{st.session_state.last_decision_id}"):
        st.session_state.correction_mode = True
        st.rerun()

if st.session_state.correction_mode:
    with st.form("correction_form"):
        st.write("**Sorry about that. How should I have responded?**")
        correction_text = st.text_area("Your ideal response:", key="correction")
        if st.form_submit_button("Submit & Teach"):
            with st.spinner("🧠 Learning from your feedback..."):
                st.session_state.agent.provide_feedback(
                    st.session_state.last_decision_id, 
                    rating=1, 
                    feedback_text=correction_text
                )
            st.toast("Thank you! I've updated my internal rules.", icon="🧠")
            st.session_state.correction_mode = False
            st.session_state.last_decision_id = None
            st.rerun()
