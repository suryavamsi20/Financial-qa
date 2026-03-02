from __future__ import annotations

import uuid
import json
import re
from io import BytesIO
from threading import Lock
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from ollama_client import OllamaQAClient
from parser import chunk_text, extract_document_text
from vector_store import SearchResult, SimpleVectorStore

app = FastAPI(title="Financial QA API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_documents: dict[str, dict[str, Any]] = {}
_lock = Lock()


class AskRequest(BaseModel):
    document_id: str = Field(..., description="Document id returned by upload endpoint")
    question: str = Field(..., min_length=1, description="User question")
    model: str = Field(default="smollm2:135m", description="Ollama model")
    top_k: int = Field(default=4, ge=1, le=12, description="Number of chunks to retrieve")


class AskResponse(BaseModel):
    answer: str
    document_id: str
    model: str
    retrieved_chunks: list[dict[str, Any]]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/models")
def list_models() -> dict[str, list[str]]:
    try:
        models = OllamaQAClient().list_models()
        return {"models": models}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not list models: {exc}") from exc


@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(1200),
    overlap: int = Form(200),
) -> dict[str, Any]:
    if chunk_size <= 0:
        raise HTTPException(status_code=400, detail="chunk_size must be > 0")
    if overlap < 0 or overlap >= chunk_size:
        raise HTTPException(status_code=400, detail="overlap must be >= 0 and smaller than chunk_size")

    filename = file.filename or ""
    if not filename.lower().endswith((".pdf", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only PDF/XLSX/XLS files are supported")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        text = extract_document_text(BytesIO(payload), filename=filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse document: {exc}") from exc

    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        raise HTTPException(status_code=400, detail="No text content found in document")

    store = SimpleVectorStore()
    store.add_texts(
        chunks,
        metadatas=[{"source": filename, "chunk_id": idx} for idx, _ in enumerate(chunks)],
    )

    metadata = _extract_metadata(text, filename)
    document_id = uuid.uuid4().hex
    with _lock:
        _documents[document_id] = {
            "filename": filename,
            "store": store,
            "chunk_count": len(chunks),
            "metadata": metadata,
        }

    return {
        "document_id": document_id,
        "filename": filename,
        "chunk_count": len(chunks),
        "metadata": metadata,
    }


def _serialize_result(result: SearchResult) -> dict[str, Any]:
    return {"text": result.text, "score": result.score, "metadata": result.metadata}


def _extract_metadata(text: str, filename: str) -> dict[str, str]:
    fiscal = re.search(r"\b(FY\s?\d{4}|20\d{2})\b", text, flags=re.IGNORECASE)
    currency = re.search(r"\b(USD|INR|EUR|GBP|JPY|AED)\b", text, flags=re.IGNORECASE)
    entity = re.search(r"(?:Entity|Company|Issuer)\s*:\s*([^\n\.]+)", text, flags=re.IGNORECASE)

    return {
        "fiscal_year": (fiscal.group(1).upper() if fiscal else "Unknown"),
        "currency": (currency.group(1).upper() if currency else "Unknown"),
        "entity_name": (entity.group(1).strip() if entity else filename),
    }


@app.post("/qa/ask", response_model=AskResponse)
def ask_question(payload: AskRequest) -> AskResponse:
    with _lock:
        doc = _documents.get(payload.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found. Upload again.")

    results = doc["store"].similarity_search(payload.question, k=payload.top_k)
    contexts = [result.text for result in results]
    if not contexts:
        raise HTTPException(status_code=400, detail="No relevant context found for this question.")

    try:
        answer = OllamaQAClient(model=payload.model).ask(payload.question, contexts)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LLM request failed: {exc}") from exc

    return AskResponse(
        answer=answer,
        document_id=payload.document_id,
        model=payload.model,
        retrieved_chunks=[_serialize_result(result) for result in results],
    )


@app.post("/qa/ask/stream")
def ask_question_stream(payload: AskRequest) -> StreamingResponse:
    with _lock:
        doc = _documents.get(payload.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found. Upload again.")

    results = doc["store"].similarity_search(payload.question, k=payload.top_k)
    contexts = [result.text for result in results]
    if not contexts:
        raise HTTPException(status_code=400, detail="No relevant context found for this question.")

    citations = [_serialize_result(result) for result in results]

    def event_stream():
        yield f"event: citations\ndata: {json.dumps(citations, ensure_ascii=True)}\n\n"
        try:
            for piece in OllamaQAClient(model=payload.model).ask_stream(payload.question, contexts):
                safe = piece.replace("\n", "\\n")
                yield f"event: token\ndata: {safe}\n\n"
        except Exception as exc:
            yield f"event: error\ndata: LLM stream failed: {str(exc).replace(chr(10), ' ')}\n\n"
            return
        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
