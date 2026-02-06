import re
from typing import List, Any, Dict

import streamlit as st
import streamlit_mermaid as stmd


from backend.core import run_llm


_MERMAID_START = re.compile(
    r"^(flowchart|graph|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|gitgraph|mindmap|timeline)\b",
    re.MULTILINE,
)

_FENCED_MERMAID = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)


def _extract_mermaid_blocks(text: str) -> list[tuple[str, bool]]:
    """
    Parse text into segments of (content, is_mermaid).
    Handles both fenced (```mermaid) and raw mermaid blocks.
    """
    segments = []
    last_end = 0

    # First, handle fenced mermaid blocks
    for match in _FENCED_MERMAID.finditer(text):
        before = text[last_end:match.start()]
        if before.strip():
            segments.append((before, False))
        segments.append((match.group(1).strip(), True))
        last_end = match.end()

    remaining = text[last_end:]

    if segments:
        if remaining.strip():
            segments.append((remaining, False))
        return segments

    # No fenced blocks — look for raw mermaid syntax
    match = _MERMAID_START.search(text)
    if not match:
        return [(text, False)]

    before = text[:match.start()]
    if before.strip():
        segments.append((before, False))

    lines = text[match.start():].split("\n")
    mermaid_lines = []
    rest_lines = []
    in_diagram = True
    for line in lines:
        if in_diagram:
            stripped = line.strip()
            if (stripped == ""
                    or line.startswith("    ")
                    or line.startswith("\t")
                    or _MERMAID_START.match(line)
                    or stripped.startswith("style ")
                    or stripped.startswith("classDef ")
                    or stripped.startswith("class ")
                    or "-->" in stripped
                    or "---" in stripped
                    or "-.->" in stripped
                    or stripped.startswith("subgraph")
                    or stripped.startswith("end")
                    or re.match(r"^\s*\w+[\[\(\{]", stripped)):
                mermaid_lines.append(line)
            else:
                in_diagram = False
                rest_lines.append(line)
        else:
            rest_lines.append(line)

    # Remove trailing empty lines from mermaid block
    while mermaid_lines and not mermaid_lines[-1].strip():
        rest_lines.insert(0, mermaid_lines.pop())

    segments.append(("\n".join(mermaid_lines).strip(), True))
    rest = "\n".join(rest_lines).strip()
    if rest:
        segments.append((rest, False))

    return segments


def _render_with_mermaid(text: str):
    """Render text, using streamlit-mermaid for diagram blocks."""
    segments = _extract_mermaid_blocks(text)
    for content, is_mermaid in segments:
        if is_mermaid:
            stmd.st_mermaid(content)
        else:
            st.markdown(content)

def _format_sources(context_docs: List[Any]) -> List[str]:
    return [
        str((meta.get("source") or "Unknown"))
        for doc in (context_docs or [])
        if (meta := (getattr(doc, "metadata", None) or {})) is not None
    ]

st.set_page_config(page_title="The Knowledge Bot", layout="centered")
st.title("The Knowledge Bot")
st.subheader("The Know It All Bot")

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
        _render_with_mermaid(msg["content"])
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

            _render_with_mermaid(answer)
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

