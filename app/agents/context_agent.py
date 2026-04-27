from app.state import AgentState
from app.tools.context_tools import (
    get_weather_context,
    get_sg_holiday_context,
    get_sg_time_context,
)

# All valid context type names the router may request
_ALL_CONTEXT_TYPES = {"time", "weather", "holiday"}


def context_agent_node(state: AgentState) -> AgentState:
    plan = state.get("manager_plan", {})

    # Honour the router's selective list; fall back to all if the key is missing
    requested: set = set(plan.get("context_needs", _ALL_CONTEXT_TYPES))

    # Guard against unknown values coming from the LLM
    requested = requested & _ALL_CONTEXT_TYPES

    # If the plan somehow produced an empty set, fetch everything so the
    # writer always has something to work with when context_agent runs.
    if not requested:
        requested = _ALL_CONTEXT_TYPES

    result = {}
    if "time" in requested:
        result["time"] = get_sg_time_context()
    if "holiday" in requested:
        result["holiday"] = get_sg_holiday_context()
    if "weather" in requested:
        result["weather"] = get_weather_context()

    result["fetched"] = sorted(requested)

    state["context_result"] = result
    state.setdefault("used_agents", []).append("context_agent")
    state.setdefault("trace", {})["context_agent"] = result
    return state