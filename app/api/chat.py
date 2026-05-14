import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.api.dependencies import get_graph
from app.schemas.chat import ChatHistoryItem, ChatHistoryResponse, ChatMessageRequest, ChatSessionResponse
from app.services.crm import save_chat_session

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/session", response_model=ChatSessionResponse)
async def create_session():
    return ChatSessionResponse(
        session_id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc),
    )


@router.post("/message")
async def send_message(body: ChatMessageRequest, graph=Depends(get_graph)):
    config = {"configurable": {"thread_id": body.session_id}}

    async def event_stream():
        async for event in graph.astream_events(
            {"messages": [HumanMessage(content=body.message)]},
            config=config,
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield f"data: {json.dumps({'token': chunk.content})}\n\n"

        snapshot = await graph.aget_state(config)
        if snapshot.values.get("lead_submitted"):
            messages = [
                {"role": "user" if msg.type == "human" else "assistant", "content": msg.content}
                for msg in snapshot.values.get("messages", [])
                if msg.type in ("human", "ai") and msg.content
            ]
            await save_chat_session(body.session_id, messages)
            yield f"data: {json.dumps({'event': 'lead_submitted'})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_history(session_id: str, graph=Depends(get_graph)):
    config = {"configurable": {"thread_id": session_id}}
    snapshot = await graph.aget_state(config)
    messages = []
    for msg in snapshot.values.get("messages", []):
        if msg.type == "human":
            messages.append(ChatHistoryItem(role="user", content=msg.content))
        elif msg.type == "ai" and msg.content:
            messages.append(ChatHistoryItem(role="assistant", content=msg.content))
    return ChatHistoryResponse(session_id=session_id, messages=messages)