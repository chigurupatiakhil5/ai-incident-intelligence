import os
import asyncio
import httpx
import psycopg2
from psycopg2.extras import RealDictCursor
from fastembed import TextEmbedding
from dotenv import load_dotenv
import mlflow
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _embedding_model

def search_similar_incidents(question: str, limit: int = 5) -> list[str]:
    model = get_embedding_model()
    query_embedding = list(model.embed([question]))[0].tolist()
    conn = psycopg2.connect(SUPABASE_DB_URL)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT text, metadata_
                FROM data_incident_vectors
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (str(query_embedding), limit))
            rows = cur.fetchall()
            return [
                f"Incident (Server: {row['metadata_'].get('server_name', 'unknown')}, "
                f"Severity: {row['metadata_'].get('severity', 'unknown')}): {row['text']}"
                for row in rows
            ]
    finally:
        conn.close()

async def generate_answer(question: str, contexts: list[str]) -> str:
    context_text = "\n\n".join(contexts) if contexts else "No relevant incidents found."
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5",
                "max_tokens": 512,
                "system": "You are an AI ops assistant. Answer questions about system incidents based on the provided incident history. Be concise.",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Based on these past incidents:\n\n{context_text}\n\nQuestion: {question}"
                    }
                ]
            }
        )
        result = response.json()
        return result["content"][0]["text"]

TEST_CASES = [
    {
        "question": "What servers had critical CPU incidents?",
        "ground_truth": "cache-01 had a critical CPU incident with CPU usage at 95%.",
    },
    {
        "question": "Which server had memory issues?",
        "ground_truth": "db-server-01 had memory issues with memory usage at 86%.",
    },
    {
        "question": "What was the highest CPU usage recorded?",
        "ground_truth": "The highest CPU usage recorded was 95% on cache-01.",
    },
]

async def main():
    print("Running RAG evaluation...\n")

    questions = []
    answers = []
    contexts = []
    ground_truths = []

    for tc in TEST_CASES:
        print(f"Q: {tc['question']}")
        retrieved = search_similar_incidents(tc["question"])
        answer = await generate_answer(tc["question"], retrieved)
        questions.append(tc["question"])
        answers.append(answer)
        contexts.append(retrieved)
        ground_truths.append(tc["ground_truth"])
        print(f"A: {answer[:120]}...")
        print()

    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import faithfulness, context_precision, context_recall
    from langchain_groq import ChatGroq

    from ragas.llms import LangchainLLMWrapper

    groq_llm = ChatGroq(
        model="llama-3.1-8b-instant",
        groq_api_key=GROQ_API_KEY,
        temperature=0,
    )
    ragas_llm = LangchainLLMWrapper(groq_llm)

    faithfulness.llm = ragas_llm
    context_precision.llm = ragas_llm
    context_recall.llm = ragas_llm

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })

    mlflow.set_experiment("rag-incident-intelligence")
    with mlflow.start_run():
        mlflow.log_param("llm_provider", "claude-haiku-4-5")
        mlflow.log_param("embedding_model", "BAAI/bge-small-en-v1.5")
        mlflow.log_param("num_test_cases", len(TEST_CASES))

        print("Scoring with RAGAS (this takes ~30 seconds)...\n")
        result = evaluate(dataset, metrics=[faithfulness, context_precision, context_recall])

        mlflow.log_metric("faithfulness", result["faithfulness"])
        mlflow.log_metric("context_precision", result["context_precision"])
        mlflow.log_metric("context_recall", result["context_recall"])

        print("\n── RAGAS Scores ──────────────────────────────")
        print(f"Faithfulness:      {result['faithfulness']:.3f}  (is answer grounded in context?)")
        print(f"Context Precision: {result['context_precision']:.3f}  (did we retrieve relevant docs?)")
        print(f"Context Recall:    {result['context_recall']:.3f}  (did we retrieve all relevant docs?)")
        print("─────────────────────────────────────────────")
        print("\nScores range 0-1. Higher is better.")
        print("\nRun logged to MLflow. View with: mlflow ui")

if __name__ == "__main__":
    asyncio.run(main())