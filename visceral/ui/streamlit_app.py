# app.py
import streamlit as st
from visceral.core.agent import VisceralAgent

# --- Page Configuration ---
st.set_page_config(
    page_title="Visceral AI",
    page_icon="🧠",
    layout="wide"
)

# --- State Management ---
# Initialize the agent and other session state variables
if 'agent' not in st.session_state:
    st.session_state.agent = VisceralAgent()
    print("INFO: Initialized a new VisceralAgent.")

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'last_decision_id' not in st.session_state:
    st.session_state.last_decision_id = None

# --- UI Rendering ---
st.title("🧠 Visceral: The Self-Correcting AI")
st.caption("An agent that evolves its logic from your feedback. Powered by symbolic rules and an LLM.")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "explanation" in message:
            with st.expander("Show Reasoning"):
                st.code(message["explanation"], language="text")

# --- Main Interaction Loop ---
if prompt := st.chat_input("What's on your mind?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process the query with the agent
    agent = st.session_state.agent
    decision = agent.process_query(prompt)
    st.session_state.last_decision_id = decision.id

    # Display agent's response
    with st.chat_message("assistant"):
        response_content = decision.output
        st.markdown(response_content)
        
        # Prepare explanation
        explanation = agent.explain_decision(decision.id)
        
        # Store message with explanation
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_content,
            "explanation": explanation
        })
        
        # Rerun to show the new message immediately
        st.rerun()


# --- Feedback Mechanism ---
if st.session_state.last_decision_id:
    st.divider()
    st.write("Was this response helpful?")
    
    col1, col2, col3 = st.columns([1, 1, 5])
    
    with col1:
        if st.button("👍 Yes"):
            agent = st.session_state.agent
            agent.provide_feedback(st.session_state.last_decision_id, rating=5)
            st.toast("Thanks for the feedback! I'll reinforce this logic.", icon="✅")
            st.session_state.last_decision_id = None # Prevent multiple feedbacks
            st.rerun()

    with col2:
        if st.button("👎 No"):
            st.session_state.correction_mode = True
            st.rerun()

# --- Correction Input Form ---
if 'correction_mode' in st.session_state and st.session_state.correction_mode:
    with st.form("correction_form"):
        st.write("Sorry about that. How should I have responded?")
        correction_text = st.text_area("Your ideal response:", key="correction")
        submitted = st.form_submit_button("Submit Correction")

        if submitted and correction_text:
            agent = st.session_state.agent
            decision_id = st.session_state.last_decision_id
            
            with st.spinner("Learning from your feedback... This might take a moment."):
                agent.provide_feedback(decision_id, rating=1, feedback_text=correction_text)
            
            st.toast("Thank you! I've updated my rules based on your correction.", icon="🧠")
            
            # Reset states
            st.session_state.correction_mode = False
            st.session_state.last_decision_id = None
            st.rerun()
