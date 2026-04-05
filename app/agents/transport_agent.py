import re
from app.state import AgentState
from app.tools.transit_tools import (
    tool_bus_arrival,
    tool_bus_stops_search,
    tool_taxi_availability,
    tool_traffic_incidents,
    tool_train_alerts,
)


def _extract_bus_stop_code(question: str):
    match = re.search(r"\b\d{5}\b", question)
    return match.group(0) if match else None


def _extract_service_no(question: str):
    match = re.search(r"\b(service\s*)?([A-Za-z]?\d+[A-Za-z]?)\b", question, re.IGNORECASE)
    if match:
        val = match.group(2)
        if val.isdigit() or any(ch.isdigit() for ch in val):
            return val
    return None


def transport_agent_node(state: AgentState) -> AgentState:
    question = state["question"].lower()
    result = {}

    if "bus stop" in question and any(k in question for k in ["find", "code", "where", "lookup"]):
        q = state["question"]
        q = q.replace("find bus stop code for", "").replace("bus stop code for", "").strip()
        result["bus_stop_lookup"] = tool_bus_stops_search(q)

    if "bus" in question and any(k in question for k in ["next", "arrival", "eta"]):
        stop_code = _extract_bus_stop_code(state["question"])
        service_no = _extract_service_no(state["question"])

        if stop_code:
            result["bus_arrival"] = tool_bus_arrival(stop_code, service_no)
        else:
            result["bus_arrival"] = {
                "error": "Missing bus stop code. Please provide a 5-digit Singapore bus stop code."
            }

    if any(k in question for k in ["traffic", "accident", "incident", "jam"]):
        result["traffic"] = tool_traffic_incidents()

    if any(k in question for k in ["train", "mrt", "disruption", "ewl", "nsl", "dtl", "ccl", "nel", "tel"]):
        result["train_status"] = tool_train_alerts()

    if any(k in question for k in ["taxi", "cab"]):
        result["taxi"] = tool_taxi_availability()

    if not result:
        result["general_transport"] = {
            "note": "No specific transport tool matched strongly. Use manager/context response."
        }

    state["transport_result"] = result
    state.setdefault("used_agents", []).append("transport_agent")
    state.setdefault("trace", {})["transport_agent"] = result
    return state