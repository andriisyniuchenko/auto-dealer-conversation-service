from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition

from app.agent.nodes import agent_node, get_tool_node, track_lead_node
from app.agent.state import State


def _route_after_tools(state: State) -> str:
    last = state["messages"][-1]
    if getattr(last, "name", None) == "submit_lead":
        return "track_lead"
    return "agent"


def build_graph(checkpointer):
    builder = StateGraph(State)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", get_tool_node())
    builder.add_node("track_lead", track_lead_node)
    builder.set_entry_point("agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_conditional_edges("tools", _route_after_tools, {"track_lead": "track_lead", "agent": "agent"})
    builder.add_edge("track_lead", "agent")
    return builder.compile(checkpointer=checkpointer)
