import os

import httpx
import streamlit as st

API_URL = os.getenv("OPSLENS_API_URL", "http://localhost:8000")

st.set_page_config(page_title="OpsLens", page_icon="🔎", layout="wide")
st.title("OpsLens")
st.caption("Hybrid operations knowledge search with reranking and verified citations")

with st.sidebar:
    st.header("About")
    st.markdown(
        "OpsLens combines **BM25 keyword search** and **semantic search**, fuses them with "
        "RRF, then reranks the candidates with a cross-encoder."
    )
    try:
        health = httpx.get(f"{API_URL}/health", timeout=10).json()
        st.success(f"API ready · {health['indexed_chunks']} chunks")
        st.caption(f"Answer mode: {health['answer_mode']}")
    except Exception:
        st.error("API unavailable. Start the FastAPI service first.")

examples = [
    "What should I check when the checkout service returns HTTP 503 errors?",
    "How do we respond to a payment retry storm?",
    "What is the difference between readiness and liveness probes?",
]

question = st.text_input("Ask an operations question", placeholder=examples[0])
selected = st.selectbox("Or choose an example", [""] + examples)
if selected and not question:
    question = selected

if st.button("Ask OpsLens", type="primary", disabled=not question):
    with st.spinner("Retrieving and reranking evidence..."):
        try:
            response = httpx.post(
                f"{API_URL}/api/v1/ask",
                json={"question": question, "top_k": 5},
                timeout=90,
            )
            response.raise_for_status()
            result = response.json()
        except Exception as exc:
            st.error(f"Request failed: {exc}")
        else:
            st.subheader("Answer")
            st.markdown(result["answer"])
            st.caption(
                f"Mode: {result['mode']} · retrieval {result['retrieval_latency_ms']:.0f} ms · "
                f"generation {result['generation_latency_ms']:.0f} ms · {result['trace_id']}"
            )

            st.subheader("Verified sources")
            for citation in result["citations"]:
                label = f"[{citation['number']}] {citation['title']} — {citation['section']}"
                with st.expander(label, expanded=True):
                    st.write(citation["quote"])
                    if citation.get("source_url"):
                        st.link_button("Open upstream source", citation["source_url"])
                    else:
                        st.code(citation["source_path"], language=None)
