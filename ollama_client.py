from __future__ import annotations

import os
from typing import Iterable

from ollama import Client


class OllamaQAClient:
    def __init__(self, model: str = "smollm2:135m", host: str | None = None) -> None:
        self.model = model
        self.client = Client(host=host or os.getenv("OLLAMA_HOST"))

    def list_models(self) -> list[str]:
        response = self.client.list()
        return [model.model for model in response.models]

    def ask(self, question: str, contexts: Iterable[str]) -> str:
        prompt = self._build_prompt(question, contexts)
        if prompt is None:
            return "No document context available. Upload a file first."

        response = self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"]

    def ask_stream(self, question: str, contexts: Iterable[str]) -> Iterable[str]:
        prompt = self._build_prompt(question, contexts)
        if prompt is None:
            yield "No document context available. Upload a file first."
            return

        stream = self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        for chunk in stream:
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content

    def _build_prompt(self, question: str, contexts: Iterable[str]) -> str | None:
        context_text = "\n\n".join(contexts).strip()
        if not context_text:
            return None

        return (
            "You are a financial analysis assistant.\n"
            "Answer ONLY using the provided context. If information is missing, say so clearly.\n\n"
            f"Context:\n{context_text}\n\n"
            f"Question:\n{question}\n"
        )
