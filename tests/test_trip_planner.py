"""
test_trip_planner.py — Integration test script for the end-to-end trip planner.

Run with:
    python -m tests.test_trip_planner

Requires a running .env with:
    GOOGLE_API_KEY       (Gemini)
    GOOGLE_MAPS_API_KEY  (Places + Directions)
    LTA_ACCOUNT_KEY      (optional — tools degrade gracefully without it)
    OPENWEATHER_API_KEY  (optional — weather degrades gracefully without it)

Each test case sends a question through the full LangGraph pipeline and prints
the answer + trace summary.  It does NOT use unittest/pytest assertions so it
can be run quickly without a test runner.
"""

import json
import sys
import os

# Allow running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.graph import commutegenie_graph


def run_case(label: str, question: str) -> None:
    print("\n" + "=" * 70)
    print(f"TEST: {label}")
    print(f"Q:    {question}")
    print("=" * 70)

    initial_state = {
        "user_id": "test_user",
        "question": question,
        "used_agents": [],
        "trace": {},
        "revision_count": 0,
    }

    try:
        result = commutegenie_graph.invoke(initial_state)

        plan = result.get("trace", {}).get("manager_plan", {})
        print(f"\nRouter decision:")
        print(f"  use_trip_planner : {plan.get('use_trip_planner')}")
        print(f"  use_transport    : {plan.get('use_transport')}")
        print(f"  use_context      : {plan.get('use_context')}")
        print(f"  intent_summary   : {plan.get('intent_summary')}")

        used = result.get("used_agents", [])
        print(f"\nAgents used: {used}")

        trip_trace = result.get("trace", {}).get("trip_planner")
        if trip_trace:
            print(f"\nTrip planner trace:")
            print(f"  origin           : {trip_trace.get('origin', {}).get('resolved')}")
            print(f"  destination      : {trip_trace.get('destination', {}).get('resolved')}")
            print(f"  modes_checked    : {trip_trace.get('modes_checked')}")
            print(f"  realtime_fetched : {trip_trace.get('realtime_fetched')}")
            print(f"  best_mode        : {trip_trace.get('best_mode')}")
            print(f"  warnings         : {trip_trace.get('warnings')}")

        critic = result.get("critic_result", {})
        print(f"\nCritic: approved={critic.get('approved')}  feedback={critic.get('feedback')}")

        print(f"\n--- FINAL ANSWER ---")
        print(result.get("final_answer", "(no answer)"))

    except Exception as exc:
        print(f"\nERROR: {exc}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # -----------------------------------------------------------------------
    # Case 1: Standard trip planning — should route to trip_planner
    # -----------------------------------------------------------------------
    run_case(
        label="Standard trip plan: Orchard → Marina Bay Sands",
        question="I want to go from Orchard Road to Marina Bay Sands. What's the best way?",
    )

    # -----------------------------------------------------------------------
    # Case 2: Trip plan with informal phrasing
    # -----------------------------------------------------------------------
    run_case(
        label="Informal trip phrasing: Jurong East → Changi Airport",
        question="How do I get to Changi Airport Terminal 2 from Jurong East MRT?",
    )

    # -----------------------------------------------------------------------
    # Case 3: Non-trip transport query — should NOT use trip_planner
    # -----------------------------------------------------------------------
    run_case(
        label="Bus arrival lookup (no trip plan)",
        question="When is the next bus at stop 83139?",
    )

    # -----------------------------------------------------------------------
    # Case 4: Context-only query — should NOT use trip_planner
    # -----------------------------------------------------------------------
    run_case(
        label="Weather/context only",
        question="Is it raining in Singapore right now?",
    )

    # -----------------------------------------------------------------------
    # Case 5: Trip plan where origin/destination is ambiguous — graceful error
    # -----------------------------------------------------------------------
    run_case(
        label="Ambiguous trip (no clear O/D)",
        question="What are the traffic conditions today?",
    )
