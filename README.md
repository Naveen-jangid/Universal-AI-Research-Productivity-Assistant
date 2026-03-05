# Universal AI Research & Productivity Assistant

> A startup-grade, production-ready Generative AI system — conversational chat, document Q&A (RAG), image analysis, speech transcription, autonomous AI agents, data analysis, and persistent long-term memory. All in one.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     STREAMLIT FRONTEND  (8501)                      │
│  Chat │ Doc Q&A │ Image Analysis │ Audio │ Data Analysis │ Agent    │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ REST API (httpx)
                     ┌──────▼──────┐
                     │    Nginx    │ (80) ← Rate limiting, WS proxy
                     └──────┬──────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                    FASTAPI BACKEND  (8000)                          │
│                                                                     │
│  /chat  /documents  /images  /audio  /data  /agent                  │
│                                                                     │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐    │
│  │RAG Pipeline│ │Doc Pipeline│ │Img Pipeline│ │ Audio Pipeline │    │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────┘    │
│  ┌────────────┐ ┌───────────────────────────────────────────────┐   │
│  │Data Pipeln.│ │         AI Agent (ReAct + Tools)              │   │
│  └────────────┘ │ web_search │ doc_retriever │ calculator │ ... │   │
│                 └───────────────────────────────────────────────┘   │
│                                                                     │
│  ┌────────────────┐ ┌─────────────────┐ ┌──────────────────────┐    │
│  │  LLM Factory   │ │Embedding Models │ │ Vision + Whisper STT │    │
│  │  (GPT-4o)      │ │(OpenAI / HF)    │ │  (GPT-4o + Whisper)  │    │
│  └────────────────┘ └─────────────────┘ └──────────────────────┘    │
└──────────────────────────┬──────────────┬───────────────────────────┘
                           │              │
              ┌────────────▼───┐  ┌───────▼──────────┐
              │   FAISS VDB    │  │ SQLite Database  │
              │  (per namespace│  │ (conversations,  │
              │   + memory)    │  │  docs, memory)   │
              └────────────────┘  └──────────────────┘
```

---

## Project Structure

```
Universal-AI-Research-Productivity-Assistant/
│
├── backend/                        # FastAPI backend
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                 # App factory, lifespan, middleware
│   │   └── routes/
│   │       ├── chat.py             # /chat/* endpoints
│   │       ├── documents.py        # /documents/* endpoints
│   │       ├── images.py           # /images/* endpoints
│   │       ├── audio.py            # /audio/* endpoints
│   │       ├── data_analysis.py    # /data/* endpoints
│   │       └── agent.py            # /agent/* endpoints
│   │
│   ├── core/
│   │   ├── config.py               # Pydantic Settings (env vars)
│   │   ├── database.py             # SQLite CRUD helpers
│   │   └── logging_config.py       # Rotating file + console logging
│   │
│   ├── models/
│   │   ├── llm.py                  # LLM factory (ChatOpenAI)
│   │   ├── embeddings.py           # OpenAI / HuggingFace embeddings
│   │   ├── vision.py               # GPT-4o vision / BLIP fallback
│   │   └── speech.py               # Whisper API / local fallback
│   │
│   ├── pipelines/
│   │   ├── document_pipeline.py    # Extract → chunk → embed → store
│   │   ├── rag_pipeline.py         # Retrieve → format → LLM answer
│   │   ├── image_pipeline.py       # Save → analyse → Q&A
│   │   ├── audio_pipeline.py       # Save → transcribe → summarise
│   │   └── data_pipeline.py        # Load → EDA → visualise → Q&A
│   │
│   ├── agents/
│   │   ├── tools.py                # LangChain custom tools
│   │   └── research_agent.py       # ReAct agent executor
│   │
│   ├── memory/
│   │   └── long_term_memory.py     # Extract → store → retrieve facts
│   │
│   ├── vectorstore/
│   │   └── faiss_store.py          # FAISS load/save/search/add
│   │
│   └── utils/
│       ├── file_handler.py         # Upload validation & storage
│       └── text_processor.py       # Clean, truncate, tokenise
│
├── frontend/                       # Streamlit frontend
│   ├── __init__.py
│   ├── app.py                      # Main entry point + routing
│   ├── pages/
│   │   ├── chat.py                 # Conversational chat page
│   │   ├── documents.py            # Document upload & RAG Q&A
│   │   ├── image_analysis.py       # Image upload & vision AI
│   │   ├── audio.py                # Audio transcription & Q&A
│   │   ├── data_analysis.py        # Dataset EDA & charts
│   │   ├── agent.py                # Autonomous agent interface
│   │   └── memory.py               # Long-term memory viewer
│   ├── components/
│   │   ├── sidebar.py              # Navigation & API config
│   │   └── chat_interface.py       # Reusable chat components
│   └── utils/
│       └── api_client.py           # Backend HTTP client (httpx)
│
├── docs/
│   └── architecture.md             # Detailed architecture diagrams
│
├── Dockerfile.backend              # Multi-stage backend image
├── Dockerfile.frontend             # Frontend image
├── docker-compose.yml              # Full stack orchestration
├── nginx.conf                      # Reverse proxy configuration
├── requirements.txt                # Full dependency list
├── requirements-backend.txt        # Backend-only deps
├── requirements-frontend.txt       # Frontend-only deps
├── .env.example                    # Environment variable template
└── README.md                       # This file
```

---

## Features

| Feature | Description | Tech |
|---------|-------------|------|
| **Conversational Chat** | Multi-turn chat with memory window | GPT-4o, LangChain |
| **Document Q&A (RAG)** | Upload PDFs/DOCX → chunk → embed → ask | FAISS, LangChain RAG |
| **Image Analysis** | Upload images → describe, detect objects | GPT-4o Vision, BLIP |
| **Speech Transcription** | Upload audio → Whisper → summarise | Whisper API, GPT-4o |
| **AI Agent** | Autonomous multi-step reasoning with tools | ReAct, LangChain Agents |
| **Data Analysis** | Upload CSV → EDA → Plotly charts → Q&A | Pandas, Plotly, LLM code gen |
| **Long-term Memory** | Persistent facts across conversations | FAISS + SQLite |

---

## Quick Start (Local)

### Prerequisites

- Python 3.11+
- OpenAI API key (get one at [platform.openai.com](https://platform.openai.com))
- (Optional) SerpAPI key for agent web search

### 1. Clone and set up

```bash
git clone https://github.com/your-org/universal-ai-assistant.git
cd universal-ai-assistant

# Create virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install all dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
nano .env
```

Minimum required:
```env
OPENAI_API_KEY=sk-your-key-here
```

### 3. Start the backend

```bash
# From project root
python -m uvicorn backend.api.main:app --reload --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 4. Start the frontend

In a second terminal:
```bash
streamlit run frontend/app.py --server.port 8501
```

Open http://localhost:8501 in your browser.

---

## Docker Deployment

### Option 1: Full stack with Docker Compose (recommended)

```bash
# 1. Copy and configure environment
cp .env.example .env
nano .env     # add your API keys

# 2. Build and start all services
docker compose up --build -d

# 3. View logs
docker compose logs -f

# 4. Stop services
docker compose down
```

Services started:
| Service | URL |
|---------|-----|
| Frontend (Streamlit) | http://localhost:8501 |
| Backend (FastAPI) | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Nginx proxy | http://localhost:80 |

### Option 2: Backend only

```bash
docker build -f Dockerfile.backend -t ai-assistant-backend .
docker run -p 8000:8000 --env-file .env ai-assistant-backend
```

### Option 3: Frontend only

```bash
docker build -f Dockerfile.frontend -t ai-assistant-frontend .
docker run -p 8501:8501 -e API_BASE_URL=http://your-backend:8000/api/v1 ai-assistant-frontend
```

---

## API Reference

### Chat

```
POST /api/v1/chat/message
{
  "message": "Explain quantum computing",
  "conversation_id": "optional-uuid",
  "session_id": "optional-session-id",
  "use_memory": true,
  "temperature": 0.7
}
```

### Document Ingestion

```
POST /api/v1/documents/upload
Content-Type: multipart/form-data
  file: <PDF/DOCX/TXT>
  namespace: "my-collection"
```

### Document Q&A

```
POST /api/v1/documents/ask
{
  "question": "What is the main thesis?",
  "namespace": "my-collection",
  "k": 5
}
```

### Image Analysis

```
POST /api/v1/images/analyse
Content-Type: multipart/form-data
  file: <image>
  prompt: "Describe this image"
```

### Audio Processing

```
POST /api/v1/audio/process
Content-Type: multipart/form-data
  file: <audio>
```

### Data Analysis

```
POST /api/v1/data/upload            # Upload CSV/Excel
GET  /api/v1/data/visualisations/{file_id}  # Get Plotly charts
GET  /api/v1/data/insights/{file_id}        # Get AI insights
POST /api/v1/data/ask               # Ask question about data
{
  "file_id": "...",
  "question": "What is the average age?"
}
```

### AI Agent

```
POST /api/v1/agent/run
{
  "task": "Research recent AI developments and summarise",
  "session_id": "optional",
  "use_memory": true
}
```

Full interactive docs: http://localhost:8000/docs

---

## Configuration Reference

All configuration is via environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | **Required.** OpenAI API key |
| `OPENAI_CHAT_MODEL` | `gpt-4o` | Chat model name |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `SERPAPI_API_KEY` | — | Optional. Web search for agent |
| `CHUNK_SIZE` | `1000` | Document chunk size (chars) |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K_RETRIEVAL` | `5` | Documents to retrieve per query |
| `MAX_UPLOAD_SIZE_MB` | `50` | Maximum file upload size |
| `MEMORY_WINDOW_SIZE` | `20` | Messages in short-term memory |
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## Agent Tools

The AI agent has access to the following tools:

| Tool | Description |
|------|-------------|
| `web_search` | Search the web via SerpAPI or DuckDuckGo |
| `document_retriever` | Search uploaded documents in FAISS |
| `calculator` | Evaluate mathematical expressions |
| `datetime_info` | Get current date and time |
| `summarise_text` | Summarise long text passages |
| `python_executor` | Execute safe Python code snippets |

---

## Supported File Formats

| Feature | Supported Formats |
|---------|------------------|
| Documents | PDF, DOCX, DOC, TXT, MD, RST |
| Images | JPG, JPEG, PNG, GIF, WebP, BMP, TIFF |
| Audio | MP3, MP4, WAV, OGG, WebM, M4A, MPEG |
| Data | CSV, TSV, XLSX, XLS, JSON, Parquet |

---

## Development

### Running tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

### Adding a new route

1. Create `backend/api/routes/new_feature.py`
2. Define your Pydantic models and FastAPI router
3. Register the router in `backend/api/main.py`
4. Create `frontend/pages/new_feature.py` with a `render()` function
5. Add the page to `frontend/components/sidebar.py` and `frontend/app.py`

### Adding a new agent tool

1. Create a class inheriting from `langchain.tools.BaseTool` in `backend/agents/tools.py`
2. Add it to `get_all_tools()` function
3. The agent will automatically use it

---

## Deployment Checklist

- [ ] Set `OPENAI_API_KEY` in `.env`
- [ ] Set a strong `SECRET_KEY` in `.env`
- [ ] Set `DEBUG=false` in production
- [ ] Configure proper `ALLOWED_ORIGINS`
- [ ] Set up TLS/HTTPS in nginx (update `nginx.conf`)
- [ ] Mount persistent Docker volumes for `uploads/`, `vectorstore/`, `memory/`
- [ ] Configure log rotation
- [ ] Set up monitoring (Prometheus + Grafana recommended)
- [ ] Review rate limits in `nginx.conf`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| LLM Framework | LangChain 0.3, LlamaIndex 0.11 |
| LLM | OpenAI GPT-4o |
| Embeddings | OpenAI text-embedding-3-small / HuggingFace |
| Vector DB | FAISS-CPU |
| Vision | GPT-4o Vision / BLIP |
| Speech | OpenAI Whisper API / openai-whisper |
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Database | SQLite |
| Proxy | Nginx |
| Containers | Docker + Docker Compose |
| Data Analysis | Pandas + Plotly |

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

*Built with ❤️ using Python, LangChain, FastAPI, and Streamlit.*
