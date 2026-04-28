"""
trip_planner_agent.py — LangGraph node for end-to-end Singapore trip planning.

Pipeline (all within a single node to keep the graph topology minimal):
  1. Parse origin + destination from the user question using the LLM.
  2. Geocode both via Google Places.
  3. Fetch route options (driving + transit) from Google Directions API.
  4. Decide which real-time signals are needed.
  5. Fetch only the required LTA / weather signals.
  6. Score and rank routes.
  7. Write a structured draft answer using the LLM.
"""

import json
import re
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from app.prompts import TRIP_PLANNER_WRITER_PROMPT, TRIP_PLANNER_FALLBACK_PROMPT
from app.services.llm_service import get_llm
from app.state import AgentState
from app.tools.route_tools import (
    geocode_location,
    get_route_options,
    classify_route_error,
    build_fallback_suggestion,
    decide_realtime_needs,
    fetch_realtime_context,
    score_routes,
    build_trip_result,
)


# ---------------------------------------------------------------------------
# LLM-based origin / destination extraction
# ---------------------------------------------------------------------------

_PARSE_SYSTEM = """
You are a location extraction assistant for Singapore commute queries.

Extract the origin and destination from the user's question.

Rules:
- Return ONLY valid JSON with exactly two keys: "origin" and "destination".
- If either cannot be determined, set it to null.
- Use the exact place name or description the user gave — do not paraphrase.
- Do not add ", Singapore" — the geocoder will handle that.
- Never add any text outside the JSON block.

Examples:
  Input:  "I want to go from Orchard Road to Marina Bay Sands"
  Output: {"origin": "Orchard Road", "destination": "Marina Bay Sands"}

  Input:  "Best route from Tampines MRT to Changi Airport Terminal 3"
  Output: {"origin": "Tampines MRT", "destination": "Changi Airport Terminal 3"}

  Input:  "How do I get to NUS from Clementi?"
  Output: {"origin": "Clementi", "destination": "NUS"}
"""


def _parse_trip_locations(question: str) -> Dict[str, Any]:
    """Use the LLM to extract origin and destination from the user question."""
    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=_PARSE_SYSTEM),
        HumanMessage(content=question),
    ])
    raw = response.content if isinstance(response.content, str) else str(response.content)
    print(f"[TripPlanner] Parse raw: {raw!r}")

    # Two-stage parse: direct JSON → regex extraction → safe fallback
    try:
        parsed = json.loads(raw)
    except Exception:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
            except Exception:
                parsed = {}
        else:
            parsed = {}

    return {
        "origin": parsed.get("origin") or None,
        "destination": parsed.get("destination") or None,
        "parse_raw": raw,
    }


# ---------------------------------------------------------------------------
# LLM-based trip answer writer
# ---------------------------------------------------------------------------

def _write_trip_answer(question: str, trip_result: Dict[str, Any]) -> str:
    """Ask the LLM to produce a structured commuter-friendly answer."""
    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=TRIP_PLANNER_WRITER_PROMPT),
        HumanMessage(content=f"""
User Question:
{question}

Trip Planning Result:
{json.dumps(trip_result, indent=2, default=str)}
"""),
    ])
    return response.content if isinstance(response.content, str) else str(response.content)


def _write_trip_fallback(question: str, fallback_result: Dict[str, Any]) -> str:
    """Write a helpful response when the Directions API is unavailable."""
    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=TRIP_PLANNER_FALLBACK_PROMPT),
        HumanMessage(content=f"""
User Question:
{question}

Origin: {fallback_result.get('origin', {}).get('resolved', 'unknown')}
Destination: {fallback_result.get('destination', {}).get('resolved', 'unknown')}

General Guidance:
{json.dumps(fallback_result.get('general_guidance', {}), indent=2)}

Real-time Conditions Fetched:
{json.dumps(fallback_result.get('realtime', {}), indent=2, default=str)}
"""),
    ])
    return response.content if isinstance(response.content, str) else str(response.content)


# ---------------------------------------------------------------------------
# Main node
# ---------------------------------------------------------------------------

def trip_planner_node(state: AgentState) -> AgentState:
    question = state["question"]
    print(f"[TripPlanner] Starting for: {question!r}")

    # ---- 1. Parse locations -----------------------------------------------
    locations = _parse_trip_locations(question)
    origin_query = locations.get("origin")
    dest_query = locations.get("destination")

    if not origin_query or not dest_query:
        trip_result: Dict[str, Any] = {
            "error": "Could not extract origin or destination from the query.",
            "parse_result": locations,
            "origin": {"query": origin_query, "matched": False},
            "destination": {"query": dest_query, "matched": False},
        }
        state["trip_result"] = trip_result
        state["draft_answer"] = (
            "I could not identify a clear origin and destination in your question. "
            "Please rephrase as: \"I want to go from [origin] to [destination].\""
        )
        state.setdefault("used_agents", []).append("trip_planner")
        state.setdefault("trace", {})["trip_planner"] = trip_result
        return state

    print(f"[TripPlanner] Origin: {origin_query!r}  Destination: {dest_query!r}")

    # ---- 2. Geocode both endpoints ----------------------------------------
    origin_geo = geocode_location(origin_query)
    dest_geo = geocode_location(dest_query)

    if not origin_geo.get("matched"):
        trip_result = {
            "error": f"Could not geocode origin: {origin_query}. {origin_geo.get('error','')}",
            "origin": origin_geo,
            "destination": dest_geo,
        }
        state["trip_result"] = trip_result
        state["draft_answer"] = (
            f"I could not find '{origin_query}' on the map. "
            "Please try a more specific Singapore address or landmark name."
        )
        state.setdefault("used_agents", []).append("trip_planner")
        state.setdefault("trace", {})["trip_planner"] = trip_result
        return state

    if not dest_geo.get("matched"):
        trip_result = {
            "error": f"Could not geocode destination: {dest_query}. {dest_geo.get('error','')}",
            "origin": origin_geo,
            "destination": dest_geo,
        }
        state["trip_result"] = trip_result
        state["draft_answer"] = (
            f"I could not find '{dest_query}' on the map. "
            "Please try a more specific Singapore address or landmark name."
        )
        state.setdefault("used_agents", []).append("trip_planner")
        state.setdefault("trace", {})["trip_planner"] = trip_result
        return state

    print(f"[TripPlanner] Origin resolved: {origin_geo['name']}")
    print(f"[TripPlanner] Dest resolved:   {dest_geo['name']}")

    # ---- 3. Fetch route options -------------------------------------------
    route_results = get_route_options(
        origin=origin_geo["name"],
        destination=dest_geo["name"],
        modes=["driving", "transit"],
    )

    error_class, error_detail = classify_route_error(route_results)
    valid_modes = [
        m for m, d in route_results.items()
        if isinstance(d, dict) and "error" not in d
    ]
    print(f"[TripPlanner] Route error class: {error_class}  Valid modes: {valid_modes}")

    # ---- API-level failure (key missing / billing / not enabled) ----------
    if error_class == "api_denied":
        print(f"[TripPlanner] Directions API denied — using fallback path")
        # Still fetch LTA real-time signals so we can give useful current info
        fallback_needs = {
            "traffic": False,
            "train_alerts": True,
            "bus_stops": True,
            "bus_arrivals": False,
            "taxi": True,
            "weather": False,
            "time": True,
        }
        realtime = fetch_realtime_context(fallback_needs, origin_coords=origin_geo)
        print(f"[TripPlanner] Fallback realtime signals: {list(realtime.keys())}")

        trip_result = build_fallback_suggestion(
            origin_query=origin_query,
            destination_query=dest_query,
            realtime=realtime,
            api_error_detail=error_detail,
        )
        trip_result["origin"] = {
            "query": origin_query,
            "resolved": origin_geo.get("name", origin_query),
            "matched": True,
        }
        trip_result["destination"] = {
            "query": dest_query,
            "resolved": dest_geo.get("name", dest_query),
            "matched": True,
        }
        draft = _write_trip_fallback(question, trip_result)

        state["trip_result"] = trip_result
        state["draft_answer"] = draft
        state.setdefault("used_agents", []).append("trip_planner")
        state.setdefault("trace", {})["trip_planner"] = {
            "origin": trip_result["origin"],
            "destination": trip_result["destination"],
            "error_class": error_class,
            "api_error": error_detail,
            "realtime_fetched": list(realtime.keys()),
            "fallback": True,
        }
        return state

    # ---- No route found (ZERO_RESULTS / NOT_FOUND) ----------------------
    if error_class in ("no_route", "all_failed"):
        trip_result = {
            "error": error_detail,
            "error_class": error_class,
            "origin": {
                "query": origin_query,
                "resolved": origin_geo.get("name", origin_query),
                "matched": True,
            },
            "destination": {
                "query": dest_query,
                "resolved": dest_geo.get("name", dest_query),
                "matched": True,
            },
            "route_results": {
                m: d.get("api_status", d.get("error", "unknown"))
                for m, d in route_results.items()
            },
        }
        state["trip_result"] = trip_result
        state["draft_answer"] = (
            f"No route could be found from '{origin_geo.get('name', origin_query)}' "
            f"to '{dest_geo.get('name', dest_query)}'. "
            f"Both locations were found on the map, but the Directions API returned "
            f"no result for the requested travel modes. "
            f"Please verify the addresses are in Singapore and try rephrasing."
        )
        state.setdefault("used_agents", []).append("trip_planner")
        state.setdefault("trace", {})["trip_planner"] = trip_result
        return state

    # ---- 4. At least one valid mode — normal path -------------------------
    needs = decide_realtime_needs(route_results)
    print(f"[TripPlanner] Real-time needs: {needs}")

    # ---- 5. Fetch only needed real-time data ------------------------------
    realtime = fetch_realtime_context(needs, origin_coords=origin_geo)
    print(f"[TripPlanner] Real-time signals fetched: {list(realtime.keys())}")

    # ---- 6. Score routes --------------------------------------------------
    scored = score_routes(route_results, realtime)
    print(f"[TripPlanner] Scored order: {[s['mode'] for s in scored]}")

    # ---- 7. Build result payload -----------------------------------------
    trip_result = build_trip_result(
        origin_query=origin_query,
        destination_query=dest_query,
        origin_geo=origin_geo,
        destination_geo=dest_geo,
        route_results=route_results,
        realtime=realtime,
        scored_routes=scored,
    )

    # ---- 8. Write structured draft answer --------------------------------
    draft = _write_trip_answer(question, trip_result)

    state["trip_result"] = trip_result
    state["draft_answer"] = draft
    state.setdefault("used_agents", []).append("trip_planner")
    state.setdefault("trace", {})["trip_planner"] = {
        "origin": trip_result["origin"],
        "destination": trip_result["destination"],
        "modes_checked": [s["mode"] for s in scored],
        "realtime_fetched": list(realtime.keys()),
        "best_mode": scored[0]["mode"] if scored else None,
        "warnings": trip_result.get("warnings", []),
    }
    return state
