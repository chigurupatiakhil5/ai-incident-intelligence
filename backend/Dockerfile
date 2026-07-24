FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from fastembed import TextEmbedding; list(TextEmbedding('BAAI/bge-small-en-v1.5').embed(['test']))"

COPY . .

# Shell form (not exec-form JSON array) so $PORT actually gets substituted -
# Render assigns its own port via this env var at runtime, not always 8000.
# Falls back to 8000 for local `docker compose up`. --reload dropped: it's a
# dev-only flag (filesystem watching to auto-restart), wasted overhead and
# not meant for a production container.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}