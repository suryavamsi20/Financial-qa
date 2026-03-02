from __future__ import annotations

import requests
import streamlit as st

st.set_page_config(page_title="Financial QA App", layout="wide")
st.title("Financial Document Question Answering")
st.write("Upload a financial PDF/Excel file and ask grounded questions.")

if "document_id" not in st.session_state:
    st.session_state.document_id = None
if "document_name" not in st.session_state:
    st.session_state.document_name = ""
if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 0

with st.sidebar:
    st.header("Settings")
    api_base_url = st.text_input("FastAPI URL", value="http://127.0.0.1:8000")
    model_name = st.text_input("Ollama model", value="smollm2:135m")
    top_k = st.slider("Retrieved chunks", min_value=1, max_value=8, value=4)
    chunk_size = st.slider("Chunk size", min_value=500, max_value=4000, value=1200, step=100)
    overlap = st.slider("Chunk overlap", min_value=0, max_value=1000, value=200, step=50)

uploaded_file = st.file_uploader("Upload PDF or Excel", type=["pdf", "xlsx", "xls"])

if uploaded_file:
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")}
    data = {"chunk_size": str(chunk_size), "overlap": str(overlap)}
    with st.spinner("Uploading and indexing document..."):
        try:
            response = requests.post(
                f"{api_base_url.rstrip('/')}/documents/upload",
                files=files,
                data=data,
                timeout=120,
            )
        except requests.RequestException as exc:
            st.error(f"Could not reach backend: {exc}")
            response = None

    if response is not None:
        if response.ok:
            payload = response.json()
            st.session_state.document_id = payload["document_id"]
            st.session_state.document_name = payload["filename"]
            st.session_state.chunk_count = payload["chunk_count"]
            st.success(
                f"Document processed: {st.session_state.document_name} "
                f"({st.session_state.chunk_count} chunks)"
            )
        else:
            detail = response.json().get("detail", response.text)
            st.error(f"Upload failed: {detail}")

question = st.text_input("Ask a question about the document:")

if question:
    if not st.session_state.document_id:
        st.error("Upload a document first.")
    else:
        with st.spinner("Generating answer..."):
            try:
                response = requests.post(
                    f"{api_base_url.rstrip('/')}/qa/ask",
                    json={
                        "document_id": st.session_state.document_id,
                        "question": question,
                        "model": model_name,
                        "top_k": top_k,
                    },
                    timeout=180,
                )
            except requests.RequestException as exc:
                st.error(f"Could not reach backend: {exc}")
                response = None

        if response is not None:
            if response.ok:
                payload = response.json()
                st.subheader("Answer")
                st.write(payload["answer"])

                with st.expander("Retrieved context"):
                    for idx, chunk in enumerate(payload.get("retrieved_chunks", []), start=1):
                        st.markdown(
                            f"Chunk {idx} | score={chunk['score']:.3f} | metadata={chunk['metadata']}"
                        )
                        st.write(chunk["text"])
            else:
                detail = response.json().get("detail", response.text)
                st.error(f"Question failed: {detail}")
