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


def _extract_service_no(question: str, bus_stop_code: str | None = None):
    """
    Extract service numbers like:
    - 190
    - 36
    - 196A
    - NR6
    - service 190
    - bus 36

    But do NOT return the 5-digit bus stop code.
    """
    patterns = [
        r"\bservice\s+([A-Za-z]{0,2}\d+[A-Za-z]?)\b",
        r"\bbus\s+([A-Za-z]{0,2}\d+[A-Za-z]?)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            candidate = match.group(1)
            if candidate != bus_stop_code:
                return candidate

    candidates = re.findall(r"\b[A-Za-z]{0,2}\d+[A-Za-z]?\b", question, re.IGNORECASE)
    for candidate in candidates:
        if candidate == bus_stop_code:
            continue
        if re.fullmatch(r"\d{5}", candidate):
            continue
        return candidate

    return None


def _clean_bus_stop_lookup_query(question: str) -> str:
    q = question.strip()

    patterns_to_remove = [
        r"(?i)^find\s+bus\s+stop\s+code\s+for\s+",
        r"(?i)^bus\s+stop\s+code\s+for\s+",
        r"(?i)^find\s+bus\s+stop\s+for\s+",
        r"(?i)^find\s+",
        r"(?i)^lookup\s+",
        r"(?i)^where\s+is\s+",
        r"(?i)^where\s+",
    ]

    for pattern in patterns_to_remove:
        q = re.sub(pattern, "", q).strip()

    return q


def transport_agent_node(state: AgentState) -> AgentState:
    question_original = state["question"]
    question = question_original.lower()
    result = {}

    if "bus stop" in question and any(k in question for k in ["find", "code", "where", "lookup"]):
        q = _clean_bus_stop_lookup_query(question_original)
        result["bus_stop_lookup"] = tool_bus_stops_search(q)

    if "bus" in question and any(k in question for k in ["next", "arrival", "eta"]):
        stop_code = _extract_bus_stop_code(question_original)
        service_no = _extract_service_no(question_original, stop_code)

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