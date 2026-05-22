import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

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
    session_id = body.session_id

    async def event_stream():
        try:
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
            state_vals = snapshot.values
            logger.info(
                "State after stream: lead_submitted=%s appointment_booked=%s chat_complete=%s",
                state_vals.get("lead_submitted"),
                state_vals.get("appointment_booked"),
                state_vals.get("chat_complete"),
            )
            all_msgs = state_vals.get("messages", [])
            if state_vals.get("lead_submitted"):
                messages = [
                    {"role": "user" if msg.type == "human" else "assistant", "content": msg.content}
                    for msg in all_msgs
                    if msg.type in ("human", "ai") and msg.content and msg.content != "__greet__"
                ]
                crm_lead_id = state_vals.get("crm_lead_id")
                asyncio.create_task(save_chat_session(session_id, messages, lead_id=crm_lead_id))
            appointment_done = any(
                getattr(m, "name", None) == "book_appointment" and "Appointment scheduled" in (m.content or "")
                for m in all_msgs[-10:]
            )
            chat_closed = any(
                getattr(m, "name", None) == "close_chat"
                for m in all_msgs[-5:]
            )
            farewell_words = ("goodbye", "bye", "see you", "take care", "have a great", "have a good", "talk soon")
            last_ai = next(
                (m for m in reversed(all_msgs) if m.type == "ai" and m.content),
                None,
            )
            farewell_said = (
                (state_vals.get("lead_submitted") or state_vals.get("appointment_booked"))
                and last_ai is not None
                and any(w in last_ai.content.lower() for w in farewell_words)
            )
            if state_vals.get("chat_complete") or appointment_done or chat_closed or farewell_said:
                yield f"data: {json.dumps({'event': 'chat_complete'})}\n\n"
        except Exception as e:
            logger.exception("Error in chat stream: %s", e)
            yield f"data: {json.dumps({'event': 'error'})}\n\n"

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