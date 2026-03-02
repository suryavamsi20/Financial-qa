# Financial QA (FastAPI + Streamlit + Next.js)

Financial document Q&A system using a FastAPI backend, a Streamlit client, and a Next.js RedSun dashboard.

Repository: [https://github.com/suryavamsi20/Financial-qa](https://github.com/suryavamsi20/Financial-qa)

## Architecture

1. Frontend uploads document and sends user question.
2. FastAPI ingests file, parses text, chunks content, and builds in-memory retrieval index.
3. FastAPI retrieves top relevant chunks for each question.
4. FastAPI calls local Ollama model and returns grounded answer + retrieved chunks.
5. Optional SSE endpoint streams answer tokens in real time.

## Project Structure

- `app.py`: Streamlit frontend client.
- `frontend/`: Next.js RedSun dashboard integrated with FastAPI endpoints.
- `backend/main.py`: FastAPI backend API.
- `parser.py`: PDF/Excel extraction and chunking.
- `vector_store.py`: lexical similarity retrieval store.
- `ollama_client.py`: Ollama chat wrapper.
- `ingest.py`: optional CLI ingestion to JSON index.
- `utils/`: legacy modules from initial prototype.

## Requirements

- Python 3.10+
- Ollama installed and running locally
- Pulled model (default `smollm2:135m`)

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```powershell
ollama pull smollm2:135m
```

## Run Backend (FastAPI)

```powershell
.\venv\Scripts\uvicorn.exe backend.main:app --host 127.0.0.1 --port 8001 --reload
```

API docs:
- Swagger UI: `http://127.0.0.1:8001/docs`
- Health: `http://127.0.0.1:8001/health`

## Run Frontend (Streamlit)

```powershell
.\venv\Scripts\streamlit.exe run app.py
```

Open `http://localhost:8501`.
Keep `FastAPI URL` in sidebar as `http://127.0.0.1:8001`.

## Run Frontend (Next.js RedSun Dashboard)

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

Set backend URL for Next.js in `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8001
```

## API Endpoints

1. `GET /health`
2. `GET /models`
3. `POST /documents/upload`
4. `POST /qa/ask`
5. `POST /qa/ask/stream` (SSE)

## Optional CLI Ingestion

```powershell
.\venv\Scripts\python.exe ingest.py --input .\sample.xlsx --output .\index.json
```

## Notes

- Backend document index is in-memory for now; restarting FastAPI clears uploaded docs.
- Retrieval is lexical TF-cosine, not embedding semantic retrieval yet.
