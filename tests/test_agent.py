import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import END

from app.agent.graph import (
    _route_after_detect_test_drive,
    _route_after_extract_datetime,
    _route_after_extract_phone,
    _route_after_track_interest,
    _route_after_tools,
    _route_entry,
)
from app.agent.nodes import (
    ask_datetime_node,
    ask_name_node,
    ask_test_drive_node,
    detect_test_drive_node,
    farewell_node,
    greet_node,
    track_interest_node,
)


# ---------------------------------------------------------------------------
# _route_entry
# ---------------------------------------------------------------------------

def test_route_entry_greet():
    state = {"messages": [HumanMessage(content="__greet__")]}
    assert _route_entry(state) == "greet"


def test_route_entry_chat_complete():
    state = {"messages": [HumanMessage(content="hi")], "chat_complete": True}
    assert _route_entry(state) == END


def test_route_entry_appointment_booked():
    state = {"messages": [HumanMessage(content="hi")], "appointment_booked": True}
    assert _route_entry(state) == "farewell"


def test_route_entry_extract_datetime():
    state = {
        "messages": [HumanMessage(content="tomorrow at 2pm")],
        "asked_for_datetime": True,
        "appointment_at": None,
    }
    assert _route_entry(state) == "extract_datetime"


def test_route_entry_ask_datetime():
    state = {
        "messages": [HumanMessage(content="yes")],
        "wants_test_drive": True,
        "asked_for_datetime": False,
    }
    assert _route_entry(state) == "ask_datetime"


def test_route_entry_farewell_when_no_test_drive():
    state = {"messages": [HumanMessage(content="no thanks")], "wants_test_drive": False}
    assert _route_entry(state) == "farewell"


def test_route_entry_detect_test_drive():
    state = {
        "messages": [HumanMessage(content="maybe")],
        "lead_submitted": True,
        "test_drive_asked": True,
        "wants_test_drive": None,
    }
    assert _route_entry(state) == "detect_test_drive"


def test_route_entry_ask_test_drive():
    state = {
        "messages": [HumanMessage(content="hi")],
        "lead_submitted": True,
        "test_drive_asked": False,
    }
    assert _route_entry(state) == "ask_test_drive"


def test_route_entry_submit_lead():
    state = {
        "messages": [HumanMessage(content="hi")],
        "customer_interest": "Tesla Model 3",
        "lead_submitted": False,
        "customer_first_name": "John",
        "customer_phone": "555-1234",
    }
    assert _route_entry(state) == "submit_lead"


def test_route_entry_extract_phone():
    state = {
        "messages": [HumanMessage(content="555-1234")],
        "customer_interest": "Tesla Model 3",
        "lead_submitted": False,
        "asked_for_phone": True,
        "customer_phone": None,
        "customer_first_name": None,
    }
    assert _route_entry(state) == "extract_phone"


def test_route_entry_extract_name():
    state = {
        "messages": [HumanMessage(content="John Smith")],
        "customer_interest": "Tesla Model 3",
        "lead_submitted": False,
        "asked_for_name": True,
        "customer_first_name": None,
        "customer_phone": None,
    }
    assert _route_entry(state) == "extract_name"


def test_route_entry_ask_name():
    state = {
        "messages": [HumanMessage(content="I want it")],
        "customer_interest": "Tesla Model 3",
        "lead_submitted": False,
        "asked_for_name": False,
    }
    assert _route_entry(state) == "ask_name"


def test_route_entry_falls_back_to_agent():
    state = {"messages": [HumanMessage(content="do you have any trucks?")]}
    assert _route_entry(state) == "agent"


# ---------------------------------------------------------------------------
# _route_after_tools
# ---------------------------------------------------------------------------

def test_route_after_tools_express_interest():
    tool_msg = ToolMessage(content="Interest noted", name="express_interest", tool_call_id="1")
    state = {"messages": [tool_msg]}
    assert _route_after_tools(state) == "track_interest"


def test_route_after_tools_search_vehicles():
    tool_msg = ToolMessage(content="2023 Toyota Camry...", name="search_vehicles", tool_call_id="1")
    state = {"messages": [tool_msg]}
    assert _route_after_tools(state) == "agent"


# ---------------------------------------------------------------------------
# _route_after_track_interest
# ---------------------------------------------------------------------------

def test_route_after_track_interest_has_interest():
    state = {"messages": [], "customer_interest": "Tesla Model 3"}
    assert _route_after_track_interest(state) == "ask_name"


def test_route_after_track_interest_no_interest():
    state = {"messages": [], "customer_interest": None}
    assert _route_after_track_interest(state) == "agent"


# ---------------------------------------------------------------------------
# _route_after_extract_phone
# ---------------------------------------------------------------------------

def test_route_after_extract_phone_has_phone():
    state = {"messages": [], "customer_phone": "555-1234"}
    assert _route_after_extract_phone(state) == "submit_lead"


def test_route_after_extract_phone_no_phone():
    state = {"messages": [], "customer_phone": None}
    assert _route_after_extract_phone(state) == END


# ---------------------------------------------------------------------------
# _route_after_detect_test_drive
# ---------------------------------------------------------------------------

def test_route_after_detect_test_drive_yes():
    state = {"messages": [], "wants_test_drive": True}
    assert _route_after_detect_test_drive(state) == "ask_datetime"


def test_route_after_detect_test_drive_no():
    state = {"messages": [], "wants_test_drive": False}
    assert _route_after_detect_test_drive(state) == "farewell"


def test_route_after_detect_test_drive_unclear():
    state = {"messages": [], "wants_test_drive": None}
    assert _route_after_detect_test_drive(state) == END


# ---------------------------------------------------------------------------
# _route_after_extract_datetime
# ---------------------------------------------------------------------------

def test_route_after_extract_datetime_has_datetime():
    state = {"messages": [], "appointment_at": "2026-05-25T14:00:00-07:00"}
    assert _route_after_extract_datetime(state) == "book_appointment"


def test_route_after_extract_datetime_no_datetime():
    state = {"messages": [], "appointment_at": None}
    assert _route_after_extract_datetime(state) == END


# ---------------------------------------------------------------------------
# Deterministic nodes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_greet_node():
    result = await greet_node({"messages": []})
    assert "Jessica" in result["messages"][0].content


@pytest.mark.asyncio
async def test_ask_name_node():
    result = await ask_name_node({"messages": []})
    assert result["asked_for_name"] is True
    assert len(result["messages"]) == 1


@pytest.mark.asyncio
async def test_ask_datetime_node():
    result = await ask_datetime_node({"messages": []})
    assert result["asked_for_datetime"] is True
    assert len(result["messages"]) == 1


@pytest.mark.asyncio
async def test_ask_test_drive_node_after_lead():
    state = {
        "messages": [],
        "lead_submitted": True,
        "customer_first_name": "John",
        "customer_interest": "Tesla Model 3",
    }
    result = await ask_test_drive_node(state)
    assert result["test_drive_asked"] is True
    assert "John" in result["messages"][0].content
    assert "Tesla Model 3" in result["messages"][0].content


@pytest.mark.asyncio
async def test_ask_test_drive_node_without_lead():
    state = {
        "messages": [],
        "lead_submitted": False,
        "customer_interest": "Tesla Model 3",
    }
    result = await ask_test_drive_node(state)
    assert result["test_drive_asked"] is True
    assert "Tesla Model 3" in result["messages"][0].content


@pytest.mark.asyncio
async def test_farewell_node_with_appointment():
    state = {"messages": [], "appointment_booked": True, "customer_first_name": "John"}
    result = await farewell_node(state)
    assert result["chat_complete"] is True
    assert "test drive" in result["messages"][0].content.lower()
    assert "John" in result["messages"][0].content


@pytest.mark.asyncio
async def test_farewell_node_without_appointment():
    state = {"messages": [], "appointment_booked": False, "customer_first_name": ""}
    result = await farewell_node(state)
    assert result["chat_complete"] is True
    assert "pleasure" in result["messages"][0].content.lower()


# ---------------------------------------------------------------------------
# track_interest_node
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_track_interest_node_finds_interest():
    ai_msg = AIMessage(
        content="",
        tool_calls=[{
            "name": "express_interest",
            "args": {"vehicle_interest": "2023 Tesla Model 3"},
            "id": "call_123",
            "type": "tool_call",
        }],
    )
    state = {"messages": [ai_msg]}
    result = await track_interest_node(state)
    assert result["customer_interest"] == "2023 Tesla Model 3"


@pytest.mark.asyncio
async def test_track_interest_node_no_tool_calls():
    state = {"messages": [AIMessage(content="Let me search for that.")]}
    result = await track_interest_node(state)
    assert result == {}


# ---------------------------------------------------------------------------
# detect_test_drive_node — keyword matching only (no LLM)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_detect_test_drive_yes():
    state = {"messages": [HumanMessage(content="yes")]}
    result = await detect_test_drive_node(state)
    assert result["wants_test_drive"] is True


@pytest.mark.asyncio
async def test_detect_test_drive_sure():
    state = {"messages": [HumanMessage(content="sure, why not")]}
    result = await detect_test_drive_node(state)
    assert result["wants_test_drive"] is True


@pytest.mark.asyncio
async def test_detect_test_drive_no():
    state = {"messages": [HumanMessage(content="no thanks")]}
    result = await detect_test_drive_node(state)
    assert result["wants_test_drive"] is False


@pytest.mark.asyncio
async def test_detect_test_drive_nope():
    state = {"messages": [HumanMessage(content="nope")]}
    result = await detect_test_drive_node(state)
    assert result["wants_test_drive"] is False