from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd
from PyPDF2 import PdfReader


def _to_binary_stream(file_obj: str | Path | BinaryIO) -> BinaryIO:
    if isinstance(file_obj, (str, Path)):
        return open(file_obj, "rb")
    return file_obj


def extract_from_pdf(file_obj: str | Path | BinaryIO) -> str:
    stream = _to_binary_stream(file_obj)
    should_close = isinstance(file_obj, (str, Path))
    try:
        reader = PdfReader(stream)
        text_parts: list[str] = []
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts).strip()
    finally:
        if should_close:
            stream.close()


def extract_from_excel(file_obj: str | Path | BinaryIO) -> str:
    if isinstance(file_obj, (str, Path)):
        df = pd.read_excel(file_obj)
    else:
        payload = file_obj.read()
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        df = pd.read_excel(BytesIO(payload))
    return df.to_string(index=False)


def extract_document_text(file_obj: str | Path | BinaryIO, filename: str | None = None) -> str:
    resolved_name = filename or (str(file_obj) if isinstance(file_obj, (str, Path)) else "")
    lowered = resolved_name.lower()
    if lowered.endswith(".pdf"):
        return extract_from_pdf(file_obj)
    if lowered.endswith(".xlsx") or lowered.endswith(".xls"):
        return extract_from_excel(file_obj)
    raise ValueError("Unsupported file type. Please use PDF or Excel files.")


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> list[str]:
    if not text or not text.strip():
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = end - overlap
    return chunks
