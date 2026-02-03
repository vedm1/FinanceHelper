from typing import List, Any, Dict

import streamlit as st


from backend.core import run_llm

def _format_sources(context_docs: List[Any]) -> List[str]:
    return [
        str((meta.get("source") or "Unknown"))
        for doc in (context_docs or [])
        if (meta := (getattr(doc, "metadata", None) or {})) is not None
    ]

st.set_page_config(page_title="Lend Helper", layout="centered")
st.title("Lend Helper")

with st.sidebar:
    st.subheader("Session")
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.pop("messages", None)
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Ask me anything about the person or the company and I'll retrieve the docs and cite relevant sources.",
            "sources": []
        }
    ]
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources"):
                for source in msg["sources"]:
                    st.markdown(f"- {source}")

prompt = st.chat_input("Ask a question")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "sources": []})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Retrieving docs and generating an answer"):
                result: Dict[str, Any] = run_llm(prompt)
                answer = str(result.get("answer", "").strip() or "(No answer received)")
                sources = _format_sources(result.get("context", []))

            st.markdown(answer)
            if sources:
                with st.expander("Sources"):
                    for source in sources:
                        st.markdown(f"- {source}")
            st.session_state.messages.append(
                {
                    "role": "assistant", "content": answer, "sources": sources
                }
            )


        except Exception as e:
            st.error("Failed to generate an answer")
            st.exception(e)

