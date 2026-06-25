import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from agent.graph import workflow

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    role: str = "executive"          # "executive" | "consultant" | "operations"
    conversationId: str | None = None


@router.post("/query")
def query_endpoint(req: QueryRequest):
    # Generate a conversation ID on the first turn; clients echo it back on follow-ups
    conv_id = req.conversationId or str(uuid.uuid4())

    result = workflow.invoke({
        "query": req.query,
        "role": req.role,
        "conversationId": conv_id,
    })

    response = result["response"]
    response["conversationId"] = conv_id  # ensure client always gets the ID back
    return response
