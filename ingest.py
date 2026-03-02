from __future__ import annotations

import argparse
from pathlib import Path

from parser import chunk_text, extract_document_text
from vector_store import SimpleVectorStore


def ingest_file(
    input_path: str,
    output_path: str = "index.json",
    chunk_size: int = 1200,
    overlap: int = 200,
) -> None:
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"Input file not found: {source}")

    text = extract_document_text(source, filename=source.name)
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

    metadatas = [{"source": source.name, "chunk_id": idx} for idx, _ in enumerate(chunks)]
    store = SimpleVectorStore()
    store.add_texts(chunks, metadatas)
    store.save(output_path)
    print(f"Ingested {len(chunks)} chunks into {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a financial document into a local retrieval index.")
    parser.add_argument("--input", required=True, help="Path to source PDF/XLSX file")
    parser.add_argument("--output", default="index.json", help="Path to save index JSON")
    parser.add_argument("--chunk-size", type=int, default=1200, help="Chunk size in characters")
    parser.add_argument("--overlap", type=int, default=200, help="Chunk overlap in characters")
    args = parser.parse_args()

    ingest_file(
        input_path=args.input,
        output_path=args.output,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )


if __name__ == "__main__":
    main()
