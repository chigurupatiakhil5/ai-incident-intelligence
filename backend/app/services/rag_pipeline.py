import logging
import json
import httpx
import psycopg2
from psycopg2.extras import RealDictCursor
from fastembed import TextEmbedding
from app.config import settings

logger = logging.getLogger(__name__)

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _embedding_model

def search_similar_incidents(question: str, limit: int = 5) -> list[dict]:
    model = get_embedding_model()
    query_embedding = list(model.embed([question]))[0].tolist()

    conn = psycopg2.connect(settings.supabase_db_url)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT text, metadata_
                FROM data_incident_vectors
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (str(query_embedding), limit))
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

async def stream_claude(context: str, question: str):
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5",
                "max_tokens": 1024,
                "stream": True,
                "system": "You are an AI ops assistant. Answer questions about system incidents based on the provided incident history. Be concise and helpful.",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Based on these past incidents:\n\n{context}\n\nQuestion: {question}"
                    }
                ]
            }
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        event = json.loads(data)
                        if event.get("type") == "content_block_delta":
                            yield event["delta"].get("text", "")
                    except json.JSONDecodeError:
                        pass

async def stream_groq(context: str, question: str):
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "content-type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "max_tokens": 1024,
                "stream": True,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an AI ops assistant. Answer questions about system incidents based on the provided incident history. Be concise and helpful."
                    },
                    {
                        "role": "user",
                        "content": f"Based on these past incidents:\n\n{context}\n\nQuestion: {question}"
                    }
                ]
            }
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        event = json.loads(data)
                        delta = event["choices"][0]["delta"]
                        if "content" in delta and delta["content"]:
                            yield delta["content"]
                    except (json.JSONDecodeError, KeyError):
                        pass

async def stream_rag_response(question: str):
    try:
        incidents = search_similar_incidents(question)

        if incidents:
            context = "\n\n".join([
                f"Incident (Server: {inc['metadata_'].get('server_name', 'unknown')}, "
                f"Severity: {inc['metadata_'].get('severity', 'unknown')}): "
                f"{inc['text']}"
                for inc in incidents
            ])
        else:
            context = "No relevant incidents found."

        provider = settings.llm_provider.lower()
        logger.info(f"Using LLM provider: {provider}")

        if provider == "groq":
            async for token in stream_groq(context, question):
                yield token
        else:
            async for token in stream_claude(context, question):
                yield token

    except Exception as e:
        logger.error(f"RAG pipeline error: {e}")
        yield f"Error: {str(e)}"