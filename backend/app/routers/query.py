import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.rag_pipeline import stream_rag_response

router = APIRouter()

class QueryRequest(BaseModel):
    question: str

@router.post("/query")
async def query_incidents(request: QueryRequest):
    async def generate():
        async for token in stream_rag_response(request.question):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")