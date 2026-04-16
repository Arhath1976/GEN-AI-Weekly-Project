import os
import html
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from knowledgegraph import HybridKnowledgeGraphRAG


def render_copyable_block(block_title: str, content: str, block_key: str, height: int = 180) -> None:
        """Render a copyable evidence block with a plain text Copy action."""
        safe_text = content or ""
        escaped_text = html.escape(safe_text)
        js_text = json.dumps(safe_text)
        component_html = f"""
        <div style=\"border:1px solid #d1d5db;border-radius:10px;background:#f3f4f6;\">
            <div style=\"display:flex;justify-content:space-between;align-items:center;padding:8px 10px;border-bottom:1px solid #d1d5db;background:#f9fafb;\">
                <strong style=\"font-size:14px;color:#111111;\">{html.escape(block_title)}</strong>
                <button id=\"copy-{block_key}\" type=\"button\" style=\"border:none;background:transparent;color:#111111;cursor:pointer;font-weight:600;\">Copy</button>
            </div>
            <pre style=\"margin:0;padding:10px;max-height:{height}px;overflow:auto;white-space:pre-wrap;word-break:break-word;color:#111111;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,Liberation Mono,Courier New,monospace;font-size:14px;\">{escaped_text}</pre>
        </div>
        <script>
            const btn = document.getElementById('copy-{block_key}');
            if (btn) {{
                btn.addEventListener('click', async () => {{
                    try {{
                        await navigator.clipboard.writeText({js_text});
                        const old = btn.textContent;
                        btn.textContent = 'Copied';
                        setTimeout(() => {{ btn.textContent = old; }}, 1000);
                    }} catch (e) {{
                        btn.textContent = 'Copy failed';
                        setTimeout(() => {{ btn.textContent = 'Copy'; }}, 1200);
                    }}
                }});
            }}
        </script>
        """
        components.html(component_html, height=height + 52)


st.set_page_config(page_title="Knowldege Graph RAG Explorer", page_icon="KG", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --bg-main: #f3f4f6;
        --bg-card: #ffffff;
        --bg-muted: #e5e7eb;
        --text-main: #111111;
        --border: #d1d5db;
    }

    .stApp {
        background: linear-gradient(180deg, #fafafa 0%, var(--bg-main) 100%);
        color: var(--text-main);
    }

    header[data-testid="stHeader"] {
        background: rgba(255, 255, 255, 0.0) !important;
    }

    [data-testid="collapsedControl"] {
        background: #ffffff !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: #111111 !important;
    }

    [data-testid="collapsedControl"],
    [data-testid="collapsedControl"] *,
    [data-testid="collapsedControl"] svg,
    [data-testid="collapsedControl"] svg path,
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapseButton"] *,
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stSidebarCollapseButton"] svg path,
    button[aria-label*="sidebar" i],
    button[aria-label*="sidebar" i] *,
    button[aria-label*="sidebar" i] svg,
    button[aria-label*="sidebar" i] svg path {
        color: #111111 !important;
        fill: #111111 !important;
        stroke: #111111 !important;
    }

    [data-testid="stExpandSidebarButton"],
    [data-testid="stExpandSidebarButton"] *,
    [data-testid="stExpandSidebarButton"] button,
    [data-testid="stExpandSidebarButton"] span,
    [data-testid="stExpandSidebarButton"] p,
    [data-testid="stExpandSidebarButton"] svg,
    [data-testid="stExpandSidebarButton"] svg path,
    button[kind="header"],
    button[kind="header"] * {
        color: #111111 !important;
        fill: #111111 !important;
        stroke: #111111 !important;
    }

    [data-testid="stExpandSidebarButton"] button,
    button[kind="header"] {
        background: #f3f4f6 !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] * {
        color: var(--text-main) !important;
    }

    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 1.4rem;
        max-width: 1100px;
    }

    h1, h2, h3, p, label, span, div {
        color: var(--text-main);
    }

    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] div,
    [data-testid="stNumberInput"] input {
        background-color: var(--bg-card) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }

    [data-testid="stButton"] button {
        background: #111111;
        color: #ffffff;
        border: 1px solid #111111;
        border-radius: 10px;
        font-weight: 600;
    }

    [data-testid="stButton"] button * {
        color: #ffffff !important;
        fill: #ffffff !important;
    }

    [data-testid="stButton"] button:hover {
        background: #2b2b2b;
        border-color: #2b2b2b;
    }

    [data-testid="stStatusWidget"] {
        border-radius: 10px;
    }

    .stAlert {
        border: 1px solid var(--border);
        border-radius: 10px;
        background: var(--bg-card);
    }

    [data-testid="stExpander"] {
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        background: var(--bg-card) !important;
        overflow: hidden;
    }

    [data-testid="stExpander"] details {
        background: var(--bg-card) !important;
    }

    [data-testid="stExpander"] summary {
        background: #f9fafb !important;
        color: var(--text-main) !important;
        border-bottom: 1px solid var(--border) !important;
    }

    [data-testid="stExpander"] summary * {
        color: var(--text-main) !important;
        fill: var(--text-main) !important;
        stroke: var(--text-main) !important;
    }

    [data-testid="stExpander"] details > div {
        background: var(--bg-card) !important;
    }

    [data-testid="stCodeBlock"],
    [data-testid="stCodeBlock"] pre,
    [data-testid="stCodeBlock"] code,
    .stCode,
    .stCode pre,
    .stCode code {
        background: #f3f4f6 !important;
        color: #111111 !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }

    [data-testid="stCodeBlock"] span {
        color: #111111 !important;
    }

    [data-testid="stCodeBlock"] button,
    [data-testid="stCodeBlock"] button *,
    [data-testid="stCodeBlock"] button svg,
    [data-testid="stCodeBlock"] button svg path,
    [data-testid="stCodeBlock"] button[title*="Copy" i],
    [data-testid="stCodeBlock"] button[aria-label*="Copy" i] {
        color: #ffffff !important;
        fill: #ffffff !important;
        stroke: #ffffff !important;
        background: #111111 !important;
        border: 1px solid #111111 !important;
        border-radius: 8px !important;
    }

    [data-testid="stCodeBlock"] button:hover,
    [data-testid="stCodeBlock"] button[title*="Copy" i]:hover,
    [data-testid="stCodeBlock"] button[aria-label*="Copy" i]:hover {
        background: #2b2b2b !important;
        border-color: #2b2b2b !important;
    }

    [data-testid="stCodeBlock"] button[title*="Copy" i] span,
    [data-testid="stCodeBlock"] button[aria-label*="Copy" i] span,
    [data-testid="stCodeBlock"] button[title*="Copy" i] i,
    [data-testid="stCodeBlock"] button[aria-label*="Copy" i] i,
    [data-testid="stCodeBlock"] button[title*="Copy" i] svg,
    [data-testid="stCodeBlock"] button[aria-label*="Copy" i] svg,
    [data-testid="stCodeBlock"] button[title*="Copy" i] svg path,
    [data-testid="stCodeBlock"] button[aria-label*="Copy" i] svg path,
    [data-testid="stCodeBlock"] button[title*="Copy" i] [class*="material"],
    [data-testid="stCodeBlock"] button[aria-label*="Copy" i] [class*="material"] {
        color: #ffffff !important;
        fill: #ffffff !important;
        stroke: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        opacity: 1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Knowldege Graph RAG Explorer")
st.caption("Build graph-enhanced retrieval from local documents and query it in one place.")
st.markdown("---")

with st.sidebar:
    st.header("Configuration")
    data_path = st.text_input("Data Folder", value="./data")
    persist_path = st.text_input("Artifacts Folder", value="./artifacts")

    provider = st.radio("LLM Provider", options=["Ollama", "OpenAI"], horizontal=True)

    if provider == "Ollama":
        ollama_model = st.text_input("Ollama Model", value="llama3.1")
        if ollama_model:
            os.environ["OLLAMA_MODEL"] = ollama_model
            os.environ.pop("OPENAI_API_KEY", None)
    else:
        openai_key = st.text_input("OPENAI_API_KEY", type="password")
        openai_model = st.text_input("OpenAI Model", value="gpt-4o-mini")
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
        os.environ["OPENAI_MODEL"] = openai_model
        os.environ.pop("OLLAMA_MODEL", None)

    max_graph_chunks = st.slider("Graph Extraction Chunks", min_value=10, max_value=300, value=120, step=10)

if "kg_system" not in st.session_state:
    st.session_state.kg_system = None
if "indexed" not in st.session_state:
    st.session_state.indexed = False
if "last_retrieval" not in st.session_state:
    st.session_state.last_retrieval = None

col_build, col_status = st.columns([1, 2])
with col_build:
    build_clicked = st.button("Build / Rebuild Index", type="primary", use_container_width=True)

with col_status:
    if st.session_state.indexed:
        st.success("Index ready")
    else:
        st.info("Index not built yet")

st.markdown("### Build Status")

if build_clicked:
    try:
        if not Path(data_path).exists():
            st.error(f"Data folder not found: {data_path}")
        else:
            with st.spinner("Building vector index and knowledge graph..."):
                system = HybridKnowledgeGraphRAG(data_path=data_path, persist_path=persist_path)
                docs, chunks, triples = system.index_all(max_chunks_for_graph=max_graph_chunks)
                st.session_state.kg_system = system
                st.session_state.indexed = True
            st.success(f"Indexed {docs} docs, {chunks} chunks, {triples} triples")
    except Exception as exc:
        st.session_state.indexed = False
        st.error(f"Build failed: {exc}")

st.subheader("Ask a Question")
query = st.text_area("Question", value="Who did ACME acquire?", height=100)
ask_clicked = st.button("Ask", use_container_width=True)

if ask_clicked:
    if not st.session_state.indexed or st.session_state.kg_system is None:
        st.warning("Build the index first.")
    else:
        try:
            with st.spinner("Thinking..."):
                retrieval = st.session_state.kg_system.debug_retrieval(query)
                answer = st.session_state.kg_system.answer(query)
                st.session_state.last_retrieval = retrieval
            st.markdown("### Answer")
            st.write(answer)
        except Exception as exc:
            st.error(f"Query failed: {exc}")

if st.session_state.last_retrieval:
    with st.expander("Retrieved Evidence", expanded=False):
        st.markdown("#### Graph Facts")
        render_copyable_block(
            block_title="Graph Facts",
            content=st.session_state.last_retrieval.get("graph_context") or "(no graph facts matched)",
            block_key="graph-facts",
            height=200,
        )
        st.markdown("#### Retrieved Passages")
        render_copyable_block(
            block_title="Retrieved Passages",
            content=st.session_state.last_retrieval.get("vector_context") or "(no retrieved passages)",
            block_key="retrieved-passages",
            height=260,
        )

st.markdown("---")
st.caption("Tip: For Ollama, run ollama pull llama3.1 before building.")
