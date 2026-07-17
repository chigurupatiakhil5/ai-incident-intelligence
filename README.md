# AI Incident Intelligence Platform

A full-stack AI-powered platform that ingests infrastructure metrics, detects anomalies, indexes incidents into a vector database, and answers natural language questions about your system using a RAG pipeline with streaming LLM responses.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Data Ingestion                           │
│                                                                 │
│   scripts/send_test_metrics.py                                  │
│          │                                                      │
│          ▼                                                      │
│      AWS SQS Queue                                              │
│          │                                                      │
│          ▼                                                      │
│   SQS Worker (background)                                       │
│     ├── Anomaly Detector (rule-based thresholds)                │
│     ├── PostgreSQL (incident storage)                           │
│     └── LlamaIndex + FastEmbed → Supabase pgvector             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        Query Pipeline                           │
│                                                                 │
│   React Frontend (Vite + TypeScript + Tailwind)                 │
│          │  POST /query                                         │
│          ▼                                                      │
│      FastAPI Backend                                            │
│          │                                                      │
│          ▼                                                      │
│   pgvector similarity search (psycopg2 + BAAI/bge-small-en)    │
│          │  retrieved context                                   │
│          ▼                                                      │
│   Claude Haiku / Groq LLaMA (switchable via LLM_PROVIDER)      │
│          │  SSE streaming                                       │
│          ▼                                                      │
│   React Frontend (token-by-token display)                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        Evaluation                               │
│                                                                 │
│   scripts/evaluate_rag.py                                       │
│     ├── RAGAS (faithfulness, context precision, context recall) │
│     ├── Groq LLaMA as evaluation LLM                           │
│     └── MLflow experiment tracking                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **API** | FastAPI | REST endpoints + SSE streaming |
| **Database** | PostgreSQL (Docker) | Incident storage |
| **ORM** | SQLAlchemy | Python database interface |
| **Message Queue** | AWS SQS | Decouple metric ingestion from processing |
| **AWS SDK** | boto3 | Poll SQS queue |
| **Vector Store** | Supabase pgvector | Semantic similarity search |
| **Indexing** | LlamaIndex | Index incidents into pgvector |
| **Embeddings** | FastEmbed (BAAI/bge-small-en-v1.5) | Local embedding model, no API cost |
| **Primary LLM** | Claude Haiku (Anthropic) | RAG answer generation |
| **Fallback LLM** | Groq LLaMA 3.1 8B | Free LLM fallback via env var switch |
| **HTTP Client** | httpx | Direct streaming calls to LLM APIs |
| **Evaluation** | RAGAS | Faithfulness, precision, recall scoring |
| **Experiment Tracking** | MLflow | Log and compare evaluation runs |
| **Frontend** | React + TypeScript + Vite | Browser UI |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **Containerization** | Docker + Docker Compose | Run full stack with one command |
| **CI/CD** | GitHub Actions | Auto-run checks on every push |

---

## Features

- **Real-time anomaly detection** — CPU/memory threshold rules flag warning and critical incidents automatically
- **Vector similarity search** — semantic search over indexed incidents using pgvector and local embeddings
- **Streaming RAG responses** — answers stream token-by-token directly to the browser via SSE
- **Switchable LLM provider** — change `LLM_PROVIDER=groq` in `.env` to switch from Claude to Groq with zero code changes
- **RAGAS evaluation** — automated scoring of RAG quality (faithfulness, context precision, context recall)
- **MLflow tracking** — every evaluation run logged with metrics and parameters for comparison
- **GitHub Actions CI** — backend import check and frontend build run on every push

---

## Project Structure

```
ai-incident-intelligence/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Environment variable settings
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models/
│   │   │   └── incident.py      # Incident database model
│   │   ├── routers/
│   │   │   └── query.py         # POST /query SSE endpoint
│   │   ├── services/
│   │   │   ├── anomaly_detector.py  # CPU/memory threshold rules
│   │   │   ├── indexer.py           # LlamaIndex → pgvector
│   │   │   ├── rag_pipeline.py      # Vector search + LLM streaming
│   │   │   └── sqs_consumer.py      # boto3 SQS polling
│   │   └── workers/
│   │       └── sqs_worker.py        # Background ingestion loop
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Main UI component
│   │   └── index.css            # Tailwind directives
│   ├── package.json
│   └── vite.config.ts
├── scripts/
│   ├── send_test_metrics.py     # Send fake metrics to SQS
│   ├── evaluate_rag.py          # RAGAS + MLflow evaluation
│   └── requirements-eval.txt   # Evaluation dependencies
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI pipeline
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Prerequisites

- Docker + Docker Compose
- Python 3.11+
- Node.js 20+
- AWS account (free tier) — SQS queue named `incident-metrics`
- Supabase account — project with pgvector enabled
- Anthropic API key (Claude Haiku)
- Groq API key (free)

---

## Running Locally

**1. Clone and configure environment:**

```bash
git clone https://github.com/chigurupatiakhil5/ai-incident-intelligence.git
cd ai-incident-intelligence
cp .env.example .env
# Fill in your API keys in .env
```

**2. Start the backend:**

```bash
docker compose up --build
```

**3. Send test metrics to SQS:**

```bash
python3 scripts/send_test_metrics.py
```

**4. Start the frontend:**

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` and ask questions about your incidents.

---

**5. Run RAGAS evaluation (optional):**

```bash
pip3 install -r scripts/requirements-eval.txt
python3 scripts/evaluate_rag.py
```

View results in MLflow:

```bash
/Users/chigurupati/Library/Python/3.9/bin/mlflow ui --port 5001
```

---

## Environment Variables

See `.env.example` for all required variables. Key ones:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Local PostgreSQL (Docker) |
| `ANTHROPIC_API_KEY` | From console.anthropic.com |
| `GROQ_API_KEY` | From console.groq.com |
| `LLM_PROVIDER` | `claude` or `groq` |
| `AWS_ACCESS_KEY_ID` | AWS IAM credentials |
| `SQS_QUEUE_URL` | Your SQS queue URL |
| `SUPABASE_DB_URL` | Supabase session pooler URL |

---

## Version History

| Version | What was built |
|---|---|
| v0 | FastAPI skeleton + PostgreSQL + Docker Compose |
| v1 | AWS SQS ingestion + rule-based anomaly detection |
| v2 | LlamaIndex indexing + Supabase pgvector |
| v3 | RAG pipeline + SSE streaming via Claude API |
| v4 | Switchable LLM provider (Claude primary, Groq fallback) |
| v5 | RAGAS evaluation pipeline |
| v6 | MLflow experiment tracking |
| v7 | React TypeScript frontend with real-time streaming |
| v8 | GitHub Actions CI/CD pipeline |
| v9 | README + architecture diagram + polish |
