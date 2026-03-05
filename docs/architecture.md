# Architecture — Universal AI Research & Productivity Assistant

## High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                    (Streamlit — port 8501)                           │
│                                                                      │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌───────┐ ┌──────┐ │
│  │  Chat   │ │ Doc Q&A  │ │ Image  │ │ Audio  │ │  Data │ │Agent │ │
│  │  Page   │ │   Page   │ │  Page  │ │  Page  │ │  Page │ │ Page │ │
│  └────┬────┘ └────┬─────┘ └───┬────┘ └───┬────┘ └───┬───┘ └──┬───┘ │
│       └───────────┴───────────┴───────────┴──────────┴─────────┘    │
│                              API Client (httpx)                      │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ HTTP/REST
                          ┌─────▼──────┐
                          │   Nginx    │ ◄── Rate limiting, TLS,
                          │   Proxy    │     WebSocket proxying
                          └─────┬──────┘
                                │
┌───────────────────────────────▼──────────────────────────────────────┐
│                      FastAPI BACKEND (port 8000)                     │
│                                                                      │
│  POST /api/v1/chat/message                                           │
│  POST /api/v1/documents/upload   POST /api/v1/documents/ask          │
│  POST /api/v1/images/analyse                                         │
│  POST /api/v1/audio/process                                          │
│  POST /api/v1/data/upload        GET  /api/v1/data/visualisations    │
│  POST /api/v1/agent/run                                              │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    PIPELINE LAYER                             │   │
│  │                                                              │   │
│  │  ┌──────────────┐  ┌─────────────┐  ┌────────────────────┐  │   │
│  │  │ RAG Pipeline │  │ Doc Pipeline│  │  Image Pipeline    │  │   │
│  │  │              │  │             │  │                    │  │   │
│  │  │ • Retrieve   │  │ • Extract   │  │ • GPT-4o Vision   │  │   │
│  │  │   chunks     │  │   text      │  │ • BLIP fallback   │  │   │
│  │  │ • Format ctx │  │ • Chunk     │  │ • Struct extract  │  │   │
│  │  │ • LLM answer │  │ • Embed     │  └────────────────────┘  │   │
│  │  └──────────────┘  └─────────────┘                          │   │
│  │                                                              │   │
│  │  ┌──────────────┐  ┌─────────────┐  ┌────────────────────┐  │   │
│  │  │Audio Pipeline│  │Data Pipeline│  │   Agent System     │  │   │
│  │  │              │  │             │  │                    │  │   │
│  │  │ • Whisper    │  │ • Load DF   │  │ • ReAct Agent      │  │   │
│  │  │   transcribe │  │ • EDA       │  │ • Tool selection   │  │   │
│  │  │ • Summarise  │  │ • Plotly    │  │ • Multi-step plan  │  │   │
│  │  │ • Keywords   │  │ • AI insight│  └────────────────────┘  │   │
│  │  └──────────────┘  └─────────────┘                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     MODEL LAYER                               │   │
│  │                                                              │   │
│  │  ┌────────────────┐  ┌──────────────────┐  ┌─────────────┐  │   │
│  │  │   LLM Factory  │  │ Embedding Models │  │ Vision/STT  │  │   │
│  │  │                │  │                  │  │             │  │   │
│  │  │ • ChatOpenAI   │  │ • OpenAI embed-3 │  │ • GPT-4o    │  │   │
│  │  │   (GPT-4o)     │  │ • HF sentence-   │  │   vision    │  │   │
│  │  │ • Temperature  │  │   transformers   │  │ • Whisper   │  │   │
│  │  │   control      │  │   (fallback)     │  │   API/local │  │   │
│  │  └────────────────┘  └──────────────────┘  └─────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└───────────┬───────────────────────────┬──────────────────────────────┘
            │                           │
  ┌─────────▼──────────┐    ┌───────────▼────────────────────────────┐
  │   FAISS Vector DB  │    │         SQLite Database                 │
  │                    │    │                                         │
  │ • Document chunks  │    │ • conversations                         │
  │   (per namespace)  │    │ • messages                              │
  │ • Memory facts     │    │ • documents (registry)                  │
  │                    │    │ • memory_facts                          │
  │ Namespaces:        │    │                                         │
  │ • default          │    │ Persisted to:                           │
  │ • long_term_memory │    │   memory/assistant.db                   │
  │ • [custom]         │    │                                         │
  └────────────────────┘    └─────────────────────────────────────────┘
```

## Data Flow Diagrams

### 1. Document Q&A (RAG) Pipeline

```
User uploads PDF
      │
      ▼
┌─────────────────┐
│ File Validation  │  (type, size check)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Text Extraction │  PyMuPDF → pypdf → DOCX → TXT
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Text Chunking  │  RecursiveCharacterTextSplitter
│  chunk_size=1000 │  (1000 chars, 200 overlap)
│  overlap=200     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Embedding      │  OpenAI text-embedding-3-small
│   Generation     │  OR HuggingFace sentence-transformers
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FAISS Storage   │  Persisted to disk
│  (namespace)     │  vectorstore/faiss_index/{namespace}/
└─────────────────┘

User asks question
      │
      ▼
┌─────────────────┐
│ Query Embedding  │  Same embedding model
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FAISS Similarity│  Top-K cosine similarity
│  Search (top-5)  │  with relevance scores
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Prompt Assembly  │  Context + Question → RAG prompt
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   GPT-4o LLM    │  Grounded answer with citations
└─────────────────┘
```

### 2. AI Agent Execution Flow

```
User Task Input
      │
      ▼
┌─────────────────────┐
│  Long-term Memory   │  Retrieve relevant facts
│  Context Injection  │  via FAISS semantic search
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  ReAct Agent Prompt │  System + Memory + Task
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────────────────┐
│         GPT-4o Reasoning Loop        │
│                                      │
│  Thought → Action → Observation      │
│                                      │
│  Actions (tools):                    │
│  ┌──────────────┐  ┌──────────────┐  │
│  │  web_search  │  │  doc_retriev │  │
│  │  (SerpAPI /  │  │  er (FAISS)  │  │
│  │  DuckDuckGo) │  │              │  │
│  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  │
│  │  calculator  │  │  summariser  │  │
│  │  (safe eval) │  │  (LLM-based) │  │
│  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  │
│  │  python_exec │  │  datetime    │  │
│  │  (safe eval) │  │  (system)    │  │
│  └──────────────┘  └──────────────┘  │
│                                      │
│  Max 10 iterations, 120s timeout     │
└──────────┬───────────────────────────┘
           │
           ▼
    Final Response + Reasoning Trace
```

### 3. Long-term Memory Architecture

```
Conversation Turn
      │
      ▼
┌─────────────────────┐
│  Fact Extraction LLM │  JSON: [{fact, category, importance}]
└──────────┬──────────┘
           │
      ┌────┴────┐
      │         │
      ▼         ▼
┌──────────┐ ┌──────────┐
│  SQLite  │ │  FAISS   │
│          │ │          │
│ • fact   │ │ • embed  │
│ • cat    │ │   fact   │
│ • import │ │ • store  │
│ • time   │ │   in     │
│          │ │  memory  │
│          │ │  ns      │
└──────────┘ └──────────┘

Next Query
      │
      ▼
┌─────────────────────┐
│  Semantic FAISS     │  Find related facts
│  Search on query    │  (score > 0.5)
└──────────┬──────────┘
           │
      Keyword fallback from SQLite LIKE
           │
           ▼
    Memory Context String → System Prompt
```

## Technology Stack Matrix

| Layer | Primary | Fallback/Alternative |
|-------|---------|---------------------|
| LLM | OpenAI GPT-4o | Local LLaMA via Ollama |
| Embeddings | OpenAI text-embedding-3-small | HuggingFace MiniLM-L6-v2 |
| Vision | GPT-4o Vision API | BLIP (Salesforce) |
| Speech | OpenAI Whisper API | Local openai-whisper |
| Vector DB | FAISS CPU | Chroma, Pinecone |
| Framework | LangChain 0.3 | LlamaIndex 0.11 |
| Backend | FastAPI + Uvicorn | Flask, Django |
| Frontend | Streamlit | Gradio, React |
| Database | SQLite | PostgreSQL, Redis |
| Proxy | Nginx | Traefik, Caddy |
| Container | Docker Compose | Kubernetes, ECS |

## Security Architecture

```
Internet → Nginx (rate limiting, TLS) → Services

Security measures:
• CORS restricted to known origins
• File type validation (MIME + extension)
• File size limits (50 MB default)
• No shell injection (exec with restricted builtins)
• SQL parameterised queries (no ORM injection)
• Non-root Docker user (uid 1000)
• API key auth (optional, configurable)
• Secrets via environment variables only
• GZip compression for responses
```
