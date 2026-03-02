"use client";

import { useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  BadgeCheck,
  Database,
  FileText,
  LoaderCircle,
  MessageCircle,
  Send,
  ToggleLeft,
  ToggleRight,
  UploadCloud
} from "lucide-react";

type Metadata = {
  fiscal_year: string;
  currency: string;
  entity_name: string;
};

type Citation = {
  text: string;
  score: number;
  metadata: Record<string, unknown>;
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8001";

const emptyMetadata: Metadata = {
  fiscal_year: "-",
  currency: "-",
  entity_name: "-"
};

export default function HomePage() {
  const [documentId, setDocumentId] = useState<string>("");
  const [fileName, setFileName] = useState<string>("");
  const [indexingProgress, setIndexingProgress] = useState<number>(0);
  const [vectorCount, setVectorCount] = useState<number>(0);
  const [metadata, setMetadata] = useState<Metadata>(emptyMetadata);
  const [loading, setLoading] = useState<boolean>(false);
  const [input, setInput] = useState<string>("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [showContext, setShowContext] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const canAsk = useMemo(() => input.trim().length > 0 && !!documentId && !loading, [input, documentId, loading]);

  async function handleUpload(file: File) {
    setLoading(true);
    setError("");
    setFileName(file.name);
    setIndexingProgress(15);

    const timer = setInterval(() => {
      setIndexingProgress((prev) => (prev >= 88 ? prev : prev + 8));
    }, 180);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("chunk_size", "1200");
      formData.append("overlap", "200");

      const response = await fetch(`${API_BASE_URL}/documents/upload`, {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        const detail = await readErrorMessage(response);
        throw new Error(detail || "Upload failed");
      }

      const payload = await response.json();
      setDocumentId(payload.document_id);
      setVectorCount(payload.chunk_count || 0);
      setMetadata(payload.metadata || emptyMetadata);
      setIndexingProgress(100);
    } catch (err) {
      setDocumentId("");
      setVectorCount(0);
      setMetadata(emptyMetadata);
      setIndexingProgress(0);
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      clearInterval(timer);
      setLoading(false);
    }
  }

  async function handleAsk() {
    if (!canAsk) return;
    const question = input.trim();
    setInput("");
    setError("");

    const userMessage: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      text: question
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/qa/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_id: documentId,
          question,
          model: "smollm2:135m",
          top_k: 4
        })
      });

      if (!response.ok) {
        const detail = await readErrorMessage(response);
        throw new Error(detail || "Question request failed");
      }

      const payload = await response.json();
      const assistantMessage: ChatMessage = {
        id: `a-${Date.now() + 1}`,
        role: "assistant",
        text: payload.answer || "No answer returned.",
        citations: payload.retrieved_chunks || []
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Question request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen px-4 py-4 sm:px-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-4">
        <header className="glass flex items-center justify-between rounded-lg px-4 py-3 shadow-glass">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-sun/20 p-2">
              <Activity className="h-5 w-5 text-sun" />
            </div>
            <div>
              <p className="text-sm text-white/70">Financial Intelligence Console</p>
              <h1 className="text-xl font-semibold tracking-wide">FIN-QA</h1>
            </div>
          </div>
          <div className="glass flex items-center gap-2 rounded-lg px-3 py-2">
            <BadgeCheck className="h-4 w-4 text-sun" />
            <span className="text-sm">Ollama: Connected</span>
          </div>
        </header>

        <section className="grid gap-4 lg:grid-cols-10">
          <aside className="glass rounded-lg p-4 shadow-glass lg:col-span-3">
            <h2 className="mb-4 text-lg font-semibold">Analysis Sidebar</h2>

            <label
              htmlFor="doc-upload"
              className="group block cursor-pointer rounded-lg border border-dashed border-white/20 bg-white/5 p-4 transition hover:border-sun/80"
            >
              <div className="flex items-start gap-3">
                <UploadCloud className="mt-0.5 h-5 w-5 text-sun" />
                <div>
                  <p className="font-medium">Dropzone</p>
                  <p className="text-sm text-white/70">Drag and drop .pdf/.xlsx or click to browse.</p>
                  <p className="mt-2 text-xs text-white/50">{fileName || "No file selected"}</p>
                </div>
              </div>
              <input
                id="doc-upload"
                type="file"
                accept=".pdf,.xlsx,.xls"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) void handleUpload(file);
                }}
              />
            </label>

            <div className="glass mt-4 rounded-lg p-4">
              <div className="mb-2 flex items-center gap-2">
                <LoaderCircle className={`h-4 w-4 text-sun ${loading ? "animate-spin" : ""}`} />
                <h3 className="text-sm font-semibold">Vector Status</h3>
              </div>
              <p className="text-xs text-white/60">Indexing Progress</p>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
                <div className="h-full bg-sun transition-all" style={{ width: `${indexingProgress}%` }} />
              </div>
              <div className="mt-3 flex items-center justify-between text-sm">
                <span className="text-white/70">Term-Frequency Vector Count</span>
                <span className="font-semibold text-sun">{vectorCount}</span>
              </div>
            </div>

            <div className="glass mt-4 rounded-lg p-4">
              <div className="mb-3 flex items-center gap-2">
                <Database className="h-4 w-4 text-sun" />
                <h3 className="text-sm font-semibold">Metadata Card</h3>
              </div>
              <div className="space-y-2 text-sm">
                <p>
                  <span className="text-white/60">Fiscal Year:</span> {metadata.fiscal_year}
                </p>
                <p>
                  <span className="text-white/60">Currency:</span> {metadata.currency}
                </p>
                <p>
                  <span className="text-white/60">Entity Name:</span> {metadata.entity_name}
                </p>
              </div>
            </div>
          </aside>

          <section className="glass flex min-h-[70vh] flex-col rounded-lg p-4 shadow-glass lg:col-span-7">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold">QA Command Center</h2>
              <button
                type="button"
                onClick={() => setShowContext((prev) => !prev)}
                className="glass flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm hover:border-sun/60"
              >
                {showContext ? <ToggleRight className="h-4 w-4 text-sun" /> : <ToggleLeft className="h-4 w-4" />}
                Source Context
              </button>
            </div>

            <div className="glass flex-1 space-y-3 overflow-y-auto rounded-lg p-3">
              {messages.length === 0 && (
                <div className="flex h-full min-h-[280px] items-center justify-center text-center text-white/50">
                  Upload a document and ask a question to start analysis.
                </div>
              )}

              {messages.map((msg) => (
                <article
                  key={msg.id}
                  className={`rounded-lg border p-3 ${
                    msg.role === "user" ? "border-sun/40 bg-sun/10" : "border-white/15 bg-white/5"
                  }`}
                >
                  <div className="mb-1 flex items-center gap-2 text-xs uppercase tracking-wide text-white/60">
                    {msg.role === "user" ? <MessageCircle className="h-3.5 w-3.5" /> : <FileText className="h-3.5 w-3.5" />}
                    {msg.role === "user" ? "User Question" : "Ollama Response"}
                  </div>
                  <p className="text-sm leading-relaxed">{msg.text}</p>

                  {showContext && msg.role === "assistant" && msg.citations && (
                    <div className="mt-3 rounded-lg border border-white/15 bg-black/20 p-3">
                      <p className="mb-2 text-xs uppercase tracking-wide text-white/60">Retrieved Chunks</p>
                      <div className="space-y-2">
                        {msg.citations.map((c, index) => (
                          <div key={`${msg.id}-${index}`} className="rounded-md border border-white/10 bg-white/5 p-2">
                            <div className="mb-1 flex items-center justify-between text-xs">
                              <span className="text-white/60">
                                chunk-{String(c.metadata?.chunk_id ?? index + 1)}
                              </span>
                              <span className="font-medium text-sun">score: {Number(c.score || 0).toFixed(3)}</span>
                            </div>
                            <p className="text-xs text-white/80">{c.text}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </article>
              ))}
            </div>

            {error && (
              <div className="mt-3 flex items-center gap-2 rounded-lg border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            )}

            <div className="mt-4 flex items-center gap-2 rounded-lg border border-white/10 bg-black/30 p-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void handleAsk();
                }}
                placeholder={documentId ? "Ask about risks, cash flow, growth, debt, margins..." : "Upload a document first..."}
                className="w-full rounded-lg border border-white/10 bg-transparent px-3 py-2 text-sm outline-none placeholder:text-white/40 focus:border-sun/70"
              />
              <button
                type="button"
                onClick={() => void handleAsk()}
                disabled={!canAsk}
                className="inline-flex items-center gap-2 rounded-lg bg-sun px-4 py-2 text-sm font-medium text-white transition hover:bg-[#ff6f45] disabled:cursor-not-allowed disabled:bg-sun/40"
              >
                <Send className="h-4 w-4" />
                Ask AI
              </button>
            </div>
            <div className="mt-2 text-xs text-white/50">Backend: {API_BASE_URL}</div>
          </section>
        </section>
      </div>
    </main>
  );
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string") return payload.detail;
    return JSON.stringify(payload);
  } catch {
    return response.statusText || "Request failed";
  }
}
