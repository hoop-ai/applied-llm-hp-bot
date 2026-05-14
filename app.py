"""Streamlit chat UI for HP-Bot.

Run with: streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="HP-Bot", page_icon="📚", layout="centered")

st.title("📚 HP-Bot")
st.caption("A retrieval-augmented assistant for the Harry Potter book series.")

# Heavy imports happen on first script run; after that Streamlit keeps the
# module imported across reruns so subsequent turns are instant.
with st.spinner("Loading indices (first launch only — about 30 seconds) ..."):
    from src.pipeline import answer, get_pipeline_bundle
    get_pipeline_bundle()  # warms the module-level _BUNDLE singleton

from src.memory import Memory

if "memory" not in st.session_state:
    st.session_state.memory = Memory()
if "chat" not in st.session_state:
    st.session_state.chat = []

# Render existing chat
for entry in st.session_state.chat:
    role, text, debug = entry
    with st.chat_message(role):
        st.write(text)
        if debug and role == "assistant":
            with st.expander("retrieval details"):
                st.json(debug, expanded=False)

user_input = st.chat_input("Ask me about Harry Potter ...")
if user_input:
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.chat.append(("user", user_input, None))

    with st.chat_message("assistant"):
        with st.spinner("thinking ..."):
            result = answer(user_input, memory=st.session_state.memory)
        st.write(result.answer)
        with st.expander(f"retrieval details — source: {result.source}"):
            st.json(result.debug, expanded=False)

    st.session_state.chat.append(("assistant", result.answer, {"source": result.source, **result.debug}))
    st.session_state.memory.append(user_input, result.answer)

with st.sidebar:
    st.markdown("### About")
    st.markdown(
        "HP-Bot only answers questions about the Harry Potter book series, "
        "and only using the data it was given. Greetings and identity questions are allowed."
    )
    if st.button("Reset conversation"):
        st.session_state.memory = Memory()
        st.session_state.chat = []
        st.rerun()
