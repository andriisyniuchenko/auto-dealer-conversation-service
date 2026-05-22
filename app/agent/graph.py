from langgraph.graph import END, StateGraph
from langgraph.prebuilt import tools_condition

from app.agent.nodes import agent_node, get_tool_node, track_appointment_node, track_close_node, track_lead_node
from app.agent.state import State


def _route_after_tools(state: State) -> str:
    last = state["messages"][-1]
    name = getattr(last, "name", None)
    if name == "submit_lead":
        return "track_lead"
    if name == "book_appointment":
        return "track_appointment"
    if name == "close_chat":
        return "track_close"
    return "agent"


def build_graph(checkpointer):
    builder = StateGraph(State)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", get_tool_node())
    builder.add_node("track_lead", track_lead_node)
    builder.add_node("track_appointment", track_appointment_node)
    builder.add_node("track_close", track_close_node)
    builder.set_entry_point("agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_conditional_edges(
        "tools",
        _route_after_tools,
        {
            "track_lead": "track_lead",
            "track_appointment": "track_appointment",
            "track_close": "track_close",
            "agent": "agent",
        },
    )
    builder.add_edge("track_lead", "agent")
    builder.add_edge("track_appointment", "agent")
    builder.add_edge("track_close", END)
    return builder.compile(checkpointer=checkpointer)
