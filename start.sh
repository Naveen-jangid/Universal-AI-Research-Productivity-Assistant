#!/usr/bin/env bash
# ─── Local development startup script ──────────────────────────────────────
# Starts the FastAPI backend and Streamlit frontend in parallel.
# Usage: ./start.sh [--port-backend 8000] [--port-frontend 8501]

set -euo pipefail

# Defaults
PORT_BACKEND=${PORT_BACKEND:-8000}
PORT_FRONTEND=${PORT_FRONTEND:-8501}
RELOAD=${RELOAD:-true}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --port-backend) PORT_BACKEND="$2"; shift 2 ;;
    --port-frontend) PORT_FRONTEND="$2"; shift 2 ;;
    --no-reload) RELOAD=false; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Check Python is available
if ! command -v python &>/dev/null && ! command -v python3 &>/dev/null; then
  echo "❌ Python not found. Please install Python 3.11+."
  exit 1
fi

PYTHON=$(command -v python3 || command -v python)

# Check .env exists
if [ ! -f .env ]; then
  echo "⚠️  .env not found. Copying from .env.example..."
  cp .env.example .env
  echo "✏️  Please edit .env and add your OPENAI_API_KEY, then re-run this script."
  exit 1
fi

# Check OPENAI_API_KEY is set
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
  echo "⚠️  OPENAI_API_KEY does not appear to be set in .env."
  echo "   The system will use HuggingFace fallback models (slower)."
fi

# Create runtime directories
mkdir -p uploads/documents uploads/images uploads/audio uploads/data vectorstore memory logs

echo ""
echo "🚀 Starting Universal AI Research & Productivity Assistant"
echo "   Backend  → http://localhost:${PORT_BACKEND}"
echo "   Frontend → http://localhost:${PORT_FRONTEND}"
echo "   API Docs → http://localhost:${PORT_BACKEND}/docs"
echo ""

# Start backend in background
RELOAD_FLAG=""
if [ "$RELOAD" = "true" ]; then
  RELOAD_FLAG="--reload"
fi

$PYTHON -m uvicorn backend.api.main:app \
  --host 0.0.0.0 \
  --port "$PORT_BACKEND" \
  $RELOAD_FLAG \
  --log-level info \
  &
BACKEND_PID=$!

# Give backend a moment to start
sleep 3

# Start frontend
streamlit run frontend/app.py \
  --server.port "$PORT_FRONTEND" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --browser.gatherUsageStats false \
  &
FRONTEND_PID=$!

echo "✅ Both services started."
echo "   Backend PID: $BACKEND_PID | Frontend PID: $FRONTEND_PID"
echo "   Press Ctrl+C to stop both."

# Wait for either process to exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Services stopped.'" INT TERM
wait $BACKEND_PID $FRONTEND_PID
