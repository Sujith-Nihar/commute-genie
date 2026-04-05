from app.state import AgentState
from app.tools.context_tools import (
    get_mock_weather_context,
    get_sg_holiday_context,
    get_sg_time_context,
)


def context_agent_node(state: AgentState) -> AgentState:
    result = {
        "time": get_sg_time_context(),
        "holiday": get_sg_holiday_context(),
        "weather": get_mock_weather_context(),
    }

    state["context_result"] = result
    state.setdefault("used_agents", []).append("context_agent")
    state.setdefault("trace", {})["context_agent"] = result
    return state