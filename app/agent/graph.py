from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition

from app.agent.nodes import (
    agent_node,
    ask_datetime_node,
    ask_name_node,
    ask_test_drive_node,
    book_appointment_node,
    detect_test_drive_node,
    extract_datetime_node,
    extract_name_node,
    extract_phone_node,
    farewell_node,
    get_tool_node,
    greet_node,
    submit_lead_node,
    track_interest_node,
)
from app.agent.state import State

_ROUTE_TARGETS = {
    "greet": "greet",
    "agent": "agent",
    "ask_name": "ask_name",
    "extract_name": "extract_name",
    "extract_phone": "extract_phone",
    "submit_lead": "submit_lead",
    "ask_test_drive": "ask_test_drive",
    "detect_test_drive": "detect_test_drive",
    "ask_datetime": "ask_datetime",
    "extract_datetime": "extract_datetime",
    "farewell": "farewell",
    END: END,
}


def _route_entry(state: State) -> str:
    last_human = next((m for m in reversed(state["messages"]) if m.type == "human"), None)

    if last_human and last_human.content == "__greet__":
        return "greet"

    if state.get("chat_complete"):
        return END

    if state.get("appointment_booked"):
        return "farewell"

    if state.get("asked_for_datetime") and not state.get("appointment_at"):
        return "extract_datetime"

    if state.get("wants_test_drive") is True and not state.get("asked_for_datetime"):
        return "ask_datetime"

    if state.get("wants_test_drive") is False:
        return "farewell"

    if state.get("lead_submitted") and state.get("test_drive_asked") and state.get("wants_test_drive") is None:
        return "detect_test_drive"

    if state.get("lead_submitted") and not state.get("test_drive_asked"):
        return "ask_test_drive"

    interest = state.get("customer_interest")
    if interest and not state.get("lead_submitted"):
        first_name = state.get("customer_first_name")
        phone = state.get("customer_phone")

        if first_name and phone:
            return "submit_lead"

        if state.get("asked_for_phone") and not phone:
            return "extract_phone"

        if state.get("asked_for_name") and not first_name:
            return "extract_name"

        return "ask_name"

    return "agent"


def _route_after_tools(state: State) -> str:
    for msg in reversed(state["messages"]):
        if msg.type != "tool":
            break
        if getattr(msg, "name", None) == "express_interest":
            return "track_interest"
    return "agent"


def _route_after_track_interest(state: State) -> str:
    if state.get("customer_interest"):
        return "ask_name"
    return "agent"


def _route_after_extract_phone(state: State) -> str:
    if state.get("customer_phone"):
        return "submit_lead"
    return END


def _route_after_detect_test_drive(state: State) -> str:
    if state.get("wants_test_drive") is True:
        return "ask_datetime"
    if state.get("wants_test_drive") is False:
        return "farewell"
    return END


def _route_after_extract_datetime(state: State) -> str:
    if state.get("appointment_at"):
        return "book_appointment"
    return END


def build_graph(checkpointer):
    builder = StateGraph(State)

    builder.add_node("agent", agent_node)
    builder.add_node("tools", get_tool_node())
    builder.add_node("greet", greet_node)
    builder.add_node("track_interest", track_interest_node)
    builder.add_node("ask_name", ask_name_node)
    builder.add_node("extract_name", extract_name_node)
    builder.add_node("extract_phone", extract_phone_node)
    builder.add_node("submit_lead", submit_lead_node)
    builder.add_node("ask_test_drive", ask_test_drive_node)
    builder.add_node("detect_test_drive", detect_test_drive_node)
    builder.add_node("ask_datetime", ask_datetime_node)
    builder.add_node("extract_datetime", extract_datetime_node)
    builder.add_node("book_appointment", book_appointment_node)
    builder.add_node("farewell", farewell_node)

    builder.add_conditional_edges(START, _route_entry, _ROUTE_TARGETS)
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_conditional_edges("tools", _route_after_tools, {
        "track_interest": "track_interest",
        "agent": "agent",
    })
    builder.add_conditional_edges("track_interest", _route_after_track_interest, {
        "ask_name": "ask_name",
        "agent": "agent",
    })
    builder.add_conditional_edges("extract_phone", _route_after_extract_phone, {
        "submit_lead": "submit_lead",
        END: END,
    })
    builder.add_conditional_edges("detect_test_drive", _route_after_detect_test_drive, {
        "ask_datetime": "ask_datetime",
        "farewell": "farewell",
        END: END,
    })
    builder.add_conditional_edges("extract_datetime", _route_after_extract_datetime, {
        "book_appointment": "book_appointment",
        END: END,
    })

    builder.add_edge("submit_lead", "ask_test_drive")
    builder.add_edge("book_appointment", "farewell")

    builder.add_edge("greet", END)
    builder.add_edge("ask_name", END)
    builder.add_edge("extract_name", END)
    builder.add_edge("ask_test_drive", END)
    builder.add_edge("ask_datetime", END)
    builder.add_edge("farewell", END)

    return builder.compile(checkpointer=checkpointer)