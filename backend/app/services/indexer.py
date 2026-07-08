import logging
from llama_index.core import VectorStoreIndex, Document, StorageContext
from llama_index.core import Settings as LlamaSettings
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from app.config import settings

logger = logging.getLogger(__name__)

LlamaSettings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")
LlamaSettings.llm = None

_index = None

def get_index() -> VectorStoreIndex:
    global _index
    if _index is None:
        vector_store = PGVectorStore(
            connection_string=settings.supabase_db_url,
            async_connection_string=settings.supabase_db_url.replace(
                "postgresql://", "postgresql+asyncpg://"
            ),
            table_name="incident_vectors",
            schema_name="public",
            embed_dim=384,
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        _index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            storage_context=storage_context,
        )
    return _index

def index_incident(incident_id: int, server_name: str, severity: str, description: str):
    try:
        index = get_index()
        doc = Document(
            text=f"Server: {server_name}. Severity: {severity}. {description}",
            metadata={
                "incident_id": incident_id,
                "server_name": server_name,
                "severity": severity,
            }
        )
        index.insert(doc)
        logger.info(f"Indexed incident {incident_id} — {server_name}")
    except Exception as e:
        logger.error(f"Failed to index incident {incident_id}: {e}")
