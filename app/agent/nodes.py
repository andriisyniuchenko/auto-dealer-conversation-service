from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

DEALERSHIP_TZ = ZoneInfo("America/Los_Angeles")

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

from app.agent.prompts import SYSTEM_MESSAGE
from app.agent.state import State
from app.agent.tools import express_interest, search_vehicles
from app.core.llm import get_llm

tools = [search_vehicles, express_interest]
_llm = None
_extraction_llm = None
_tool_node = None


def _get_llm():
    global _llm
    if _llm is None:
        _llm = get_llm().bind_tools(tools)
    return _llm


def _get_extraction_llm():
    global _extraction_llm
    if _extraction_llm is None:
        _extraction_llm = get_llm()
    return _extraction_llm


def get_tool_node() -> ToolNode:
    global _tool_node
    if _tool_node is None:
        _tool_node = ToolNode(tools)
    return _tool_node


def _last_human_content(state: State) -> str:
    msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
    return msg.content if msg else ""


class _NameExtraction(BaseModel):
    first_name: str
    last_name: str


class _PhoneExtraction(BaseModel):
    phone: str


class _DateTimeExtraction(BaseModel):
    appointment_at: datetime


class _TestDriveIntent(BaseModel):
    wants_test_drive: bool


async def agent_node(state: State) -> dict:
    filtered = [m for m in state["messages"] if not (m.type == "human" and m.content == "__greet__")]
    messages = [SYSTEM_MESSAGE] + filtered
    try:
        response = await _get_llm().ainvoke(messages)
    except Exception:
        response = AIMessage(content="I'm sorry, could you rephrase that?")
    return {"messages": [response]}


async def greet_node(state: State) -> dict:
    return {"messages": [AIMessage(content="Hello! Welcome to Galaxy Motors. I'm Jessica — how can I help you today?")]}


async def track_interest_node(state: State) -> dict:
    for msg in reversed(state["messages"]):
        if not getattr(msg, "tool_calls", None):
            continue
        for tc in msg.tool_calls:
            if tc["name"] == "express_interest":
                return {"customer_interest": tc["args"].get("vehicle_interest")}
    return {}


async def ask_name_node(state: State) -> dict:
    return {
        "messages": [AIMessage(content="I'd love to help with that! Could I get your full name?")],
        "asked_for_name": True,
    }


async def extract_name_node(state: State) -> dict:
    text = _last_human_content(state)
    try:
        llm = _get_extraction_llm().with_structured_output(_NameExtraction)
        result = await llm.ainvoke([
            SystemMessage(content="Extract the first name and last name from this message. If only one name given, put it in first_name and leave last_name empty."),
            HumanMessage(content=text),
        ])
        return {
            "customer_first_name": result.first_name,
            "customer_last_name": result.last_name,
            "messages": [AIMessage(content=f"Nice to meet you, {result.first_name}! What's the best phone number to reach you?")],
            "asked_for_phone": True,
        }
    except Exception:
        return {"messages": [AIMessage(content="Could you share your full name?")]}


async def extract_phone_node(state: State) -> dict:
    text = _last_human_content(state)
    try:
        llm = _get_extraction_llm().with_structured_output(_PhoneExtraction)
        result = await llm.ainvoke([
            SystemMessage(content="Extract the phone number from this message. Return it as a clean string."),
            HumanMessage(content=text),
        ])
        return {"customer_phone": result.phone}
    except Exception:
        return {"messages": [AIMessage(content="Could you give me your phone number again?")]}


async def submit_lead_node(state: State) -> dict:
    from app.services.crm import submit_lead_from_chat
    lead_id = await submit_lead_from_chat(
        first_name=state.get("customer_first_name", ""),
        last_name=state.get("customer_last_name", ""),
        phone=state.get("customer_phone", ""),
        interest=state.get("customer_interest", ""),
    )
    if lead_id:
        return {"lead_submitted": True, "crm_lead_id": lead_id}
    return {}


async def ask_test_drive_node(state: State) -> dict:
    name = state.get("customer_first_name", "")
    vehicle = state.get("customer_interest") or "the vehicle"
    greeting = f", {name}" if name else ""
    if state.get("lead_submitted"):
        content = (
            f"Perfect{greeting}! We've got your details — our team will be in touch soon.\n\n"
            f"Would you like to schedule a test drive for {vehicle}?"
        )
    else:
        content = f"Would you like to schedule a test drive for {vehicle}?"
    return {
        "messages": [AIMessage(content=content)],
        "test_drive_asked": True,
    }


async def detect_test_drive_node(state: State) -> dict:
    text = _last_human_content(state).lower().strip()

    yes_words = {"yes", "yeah", "sure", "ok", "okay", "yep", "yup", "absolutely",
                 "definitely", "please", "of course", "sounds good", "love to", "why not"}
    no_words = {"no", "nope", "nah", "not", "pass", "skip", "decline", "maybe later", "no thanks"}

    if any(w in text for w in yes_words):
        return {"wants_test_drive": True}
    if any(w in text for w in no_words):
        return {"wants_test_drive": False}

    try:
        llm = _get_extraction_llm().with_structured_output(_TestDriveIntent)
        result = await llm.ainvoke([
            SystemMessage(content="The customer was asked if they want to schedule a test drive. Did they agree? Return true for yes or maybe, false for no or not interested."),
            HumanMessage(content=text),
        ])
        return {"wants_test_drive": result.wants_test_drive}
    except Exception:
        return {}


async def ask_datetime_node(state: State) -> dict:
    return {
        "messages": [AIMessage(content="What date and time works best for you?")],
        "asked_for_datetime": True,
    }


async def extract_datetime_node(state: State) -> dict:
    text = _last_human_content(state)
    now = datetime.now(DEALERSHIP_TZ)
    today = now.strftime("%Y-%m-%d")
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        llm = _get_extraction_llm().with_structured_output(_DateTimeExtraction)
        result = await llm.ainvoke([
            SystemMessage(content=(
                f"The dealership is located in Seattle (Pacific Time). Today is {today}. Tomorrow is {tomorrow}. "
                f"Extract the appointment datetime from the message and return it as a valid ISO 8601 datetime string (e.g. {today}T15:00:00). "
                f"All times are Seattle local time. "
                f"Examples: 'tomorrow at 2pm' → {tomorrow}T14:00:00, 'today at 10am' → {today}T10:00:00. "
                f"Always compute the actual date — never return relative words like 'tomorrow' or 'today'. "
                f"If only time is given, use today's date."
            )),
            HumanMessage(content=text),
        ])
        dt = result.appointment_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=DEALERSHIP_TZ)
        return {"appointment_at": dt.isoformat()}
    except Exception:
        return {"messages": [AIMessage(content="Could you give me a specific date and time? For example, 'Friday at 2pm' or 'tomorrow at 10am'.")]}


async def book_appointment_node(state: State) -> dict:
    import logging
    logger = logging.getLogger(__name__)
    from app.services.crm import book_appointment as crm_book
    crm_lead_id = state.get("crm_lead_id")
    appointment_at = state.get("appointment_at")
    logger.info("book_appointment_node: crm_lead_id=%s appointment_at=%s", crm_lead_id, appointment_at)
    if not crm_lead_id or not appointment_at:
        return {}
    ok = await crm_book(crm_lead_id, appointment_at, None)
    logger.info("book_appointment_node: crm result ok=%s", ok)
    if ok:
        return {"appointment_booked": True}
    return {}


async def farewell_node(state: State) -> dict:
    name = state.get("customer_first_name") or ""
    greeting = f", {name}" if name else ""
    if state.get("appointment_booked"):
        content = f"Wonderful{greeting}! Your test drive is all set — we look forward to seeing you. Take care!"
    else:
        content = f"It was a pleasure chatting with you{greeting}! Feel free to reach out anytime. Take care!"
    return {
        "messages": [AIMessage(content=content)],
        "chat_complete": True,
    }