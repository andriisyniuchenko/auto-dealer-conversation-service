from datetime import datetime, timezone

from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode

from app.agent.prompts import SYSTEM_MESSAGE
from app.agent.state import State
from app.agent.tools import book_appointment, close_chat, search_vehicles, submit_lead
from app.core.llm import get_llm

tools = [search_vehicles, submit_lead, book_appointment, close_chat]
_llm = None
_tool_node = None


def _get_llm():
    global _llm
    if _llm is None:
        _llm = get_llm().bind_tools(tools)
    return _llm


def get_tool_node() -> ToolNode:
    global _tool_node
    if _tool_node is None:
        _tool_node = ToolNode(tools)
    return _tool_node


async def agent_node(state: State) -> dict:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_hint = f" Today's date is {today}. When the customer gives a time like '5:30 pm', use it as-is with today's date in ISO 8601 format (e.g. {today}T17:30:00)."
    if state.get("lead_submitted"):
        crm_lead_id = state.get("crm_lead_id")
        system = SystemMessage(
            content=SYSTEM_MESSAGE.content
            + date_hint
            + " Customer details have already been passed to the team — do not submit again."
            + (f" Use lead_id={crm_lead_id} when calling book_appointment." if crm_lead_id else "")
        )
    else:
        system = SystemMessage(content=SYSTEM_MESSAGE.content + date_hint)
    messages = [system] + state["messages"]
    from langchain_core.messages import AIMessage
    try:
        response = await _get_llm().ainvoke(messages)
    except Exception:
        response = AIMessage(content="I'm sorry, could you rephrase that?")
    return {"messages": [response]}


async def track_lead_node(state: State) -> dict:
    for msg in reversed(state["messages"]):
        if not getattr(msg, "tool_calls", None):
            continue
        for tc in msg.tool_calls:
            if tc["name"] != "submit_lead":
                continue
            tool_msg = next(
                (m for m in reversed(state["messages"]) if getattr(m, "name", None) == "submit_lead"),
                None,
            )
            if tool_msg and "Lead submitted" in tool_msg.content:
                args = tc["args"]
                crm_lead_id = None
                for part in tool_msg.content.split():
                    if part.startswith("crm_lead_id="):
                        try:
                            crm_lead_id = int(part.split("=", 1)[1])
                        except ValueError:
                            pass
                return {
                    "lead_submitted": True,
                    "crm_lead_id": crm_lead_id,
                    "customer_first_name": args.get("first_name"),
                    "customer_last_name": args.get("last_name"),
                    "customer_phone": args.get("phone"),
                    "customer_email": args.get("email") or None,
                    "customer_interest": args.get("interest"),
                }
    return {}


async def track_appointment_node(state: State) -> dict:
    tool_msg = next(
        (m for m in reversed(state["messages"]) if getattr(m, "name", None) == "book_appointment"),
        None,
    )
    if tool_msg and "Appointment booked" in tool_msg.content:
        return {"appointment_booked": True, "chat_complete": True}
    return {}


async def track_close_node(state: State) -> dict:
    return {"chat_complete": True}