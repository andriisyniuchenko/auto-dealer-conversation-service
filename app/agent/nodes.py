from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode

from app.agent.prompts import SYSTEM_MESSAGE
from app.agent.state import State
from app.agent.tools import search_vehicles, submit_lead
from app.core.llm import get_llm

tools = [search_vehicles, submit_lead]
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
    if state.get("lead_submitted"):
        system = SystemMessage(
            content=SYSTEM_MESSAGE.content
            + " A lead has already been submitted for this customer — do not submit another one."
        )
    else:
        system = SYSTEM_MESSAGE
    messages = [system] + state["messages"]
    response = await _get_llm().ainvoke(messages)
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
                return {
                    "lead_submitted": True,
                    "customer_first_name": args.get("first_name"),
                    "customer_last_name": args.get("last_name"),
                    "customer_phone": args.get("phone"),
                    "customer_email": args.get("email") or None,
                    "customer_interest": args.get("interest"),
                }
    return {}