import re
from app.state import AgentState
from app.tools.transit_tools import (
    tool_bus_arrival,
    tool_bus_stops_search,
    tool_taxi_availability,
    tool_traffic_incidents,
    tool_train_alerts,
    tool_nearest_bus_stops,
    tool_nearest_ev_charging_points,
    tool_resolve_location_query,
)


def _extract_bus_stop_code(question: str):
    match = re.search(r"\b\d{5}\b", question)
    return match.group(0) if match else None


def _extract_service_no(question: str, bus_stop_code: str | None = None):
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


def _extract_location_phrase(question: str) -> str | None:
    q = question.strip()

    patterns = [
        r"(?i)\bi am at\s+(.+?)(?=,\s*what\b|,\s*where\b|,\s*show\b|\?|$)",
        r"(?i)\bi'm at\s+(.+?)(?=,\s*what\b|,\s*where\b|,\s*show\b|\?|$)",
        r"(?i)\bnearest.*?\bto\s+(.+?)(?=\?|$)",
        r"(?i)\bclosest.*?\bto\s+(.+?)(?=\?|$)",
        r"(?i)\bnear\s+(.+?)(?=\?|$)",
        r"(?i)\baround\s+(.+?)(?=\?|$)",
        r"(?i)\bat\s+(.+?)(?=\?|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            value = match.group(1).strip(" .,?")
            if value:
                return value

    return None


def transport_agent_node(state: AgentState) -> AgentState:
    question_original = state["question"]
    question = question_original.lower()
    result = {}

    has_nearest_bus = (
        "bus stop" in question
        and any(k in question for k in ["nearest", "closest", "near me"])
    )

    has_nearest_ev = (
        any(k in question for k in ["ev", "charging"])
        and any(k in question for k in ["nearest", "closest", "near me"])
    )

    location_phrase = None
    resolved_location = None

    # Only try location resolution for nearest-location queries
    if has_nearest_bus or has_nearest_ev:
        location_phrase = _extract_location_phrase(question_original)

        if location_phrase:
            resolved = tool_resolve_location_query(location_phrase)
            result["location_resolution"] = resolved

            if resolved.get("matched"):
                resolved_location = resolved.get("location")

    # 1. nearest bus stop
    if has_nearest_bus:
        if location_phrase and not resolved_location:
            result["nearest_bus_stops"] = {
                "error": f"Could not resolve the location '{location_phrase}'. Please provide a clearer Singapore landmark, address, or postal code."
            }
        else:
            result["nearest_bus_stops"] = tool_nearest_bus_stops(
                max_results=3,
                current_location=resolved_location,
            )

    # 2. nearest EV charging station
    if has_nearest_ev:
        if location_phrase and not resolved_location:
            result["nearest_ev_charging"] = {
                "error": f"Could not resolve the location '{location_phrase}'. Please provide a clearer Singapore landmark, address, or postal code."
            }
        else:
            result["nearest_ev_charging"] = tool_nearest_ev_charging_points(
                max_results=3,
                current_location=resolved_location,
            )

    # 3. bus stop code / landmark lookup
    # Skip this if the intent is clearly nearest-bus-stop
    if (
        not has_nearest_bus
        and "bus stop" in question
        and any(k in question for k in ["find", "code", "where", "lookup"])
    ):
        q = _clean_bus_stop_lookup_query(question_original)
        result["bus_stop_lookup"] = tool_bus_stops_search(q)

    # 4. bus arrival
    if "bus" in question and any(k in question for k in ["next", "arrival", "eta"]):
        stop_code = _extract_bus_stop_code(question_original)
        service_no = _extract_service_no(question_original, stop_code)

        if stop_code:
            result["bus_arrival"] = tool_bus_arrival(stop_code, service_no)
        else:
            result["bus_arrival"] = {
                "error": "Missing bus stop code. Please provide a 5-digit Singapore bus stop code."
            }

    # 5. traffic
    if any(k in question for k in ["traffic", "accident", "incident", "jam"]):
        result["traffic"] = tool_traffic_incidents()

    # 6. train / MRT
    if any(
        k in question
        for k in ["train", "mrt", "disruption", "ewl", "nsl", "dtl", "ccl", "nel", "tel"]
    ):
        result["train_status"] = tool_train_alerts()

    # 7. taxi
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