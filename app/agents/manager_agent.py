import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.prompts import MANAGER_SYSTEM_PROMPT, ROUTER_SYSTEM_PROMPT
from app.services.llm_service import get_llm
from app.state import AgentState


def _extract_router_json(text: str) -> dict:
    """Extract the routing JSON from LLM output, with a safe fallback."""
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

    # Safe fallback: call both agents so no query goes unanswered
    return {
        "use_transport": True,
        "use_context": True,
        "context_needs": ["time", "weather", "holiday"],
        "intent_summary": "Could not parse routing plan; defaulting to full agent run.",
    }


def manager_router_node(state: AgentState) -> AgentState:
    llm = get_llm()

    messages = [
        SystemMessage(content=ROUTER_SYSTEM_PROMPT),
        HumanMessage(content=f"User question: {state['question']}"),
    ]

    response = llm.invoke(messages)
    raw = response.content if isinstance(response.content, str) else str(response.content)
    plan = _extract_router_json(raw)

    # Normalise: ensure required keys always exist.
    # Use `or []` (not a default argument) so that an explicit JSON null from
    # the LLM does not reach list() as None and raise TypeError.
    raw_needs = plan.get("context_needs") or []
    normalised_plan = {
        "use_transport": bool(plan.get("use_transport", False)),
        "use_context": bool(plan.get("use_context", False)),
        "context_needs": [s.lower() for s in raw_needs if isinstance(s, str)],
        "intent_summary": plan.get("intent_summary", ""),
        "router_raw": raw,
    }

    state["manager_plan"] = normalised_plan
    state.setdefault("used_agents", []).append("manager_router")
    state.setdefault("trace", {})["manager_plan"] = normalised_plan
    return state


def manager_writer_node(state: AgentState) -> AgentState:
    llm = get_llm()

    transport_section = (
        str(state["transport_result"])
        if state.get("transport_result") is not None
        else "Not collected (transport agent was not invoked for this query)."
    )
    context_section = (
        str(state["context_result"])
        if state.get("context_result") is not None
        else "Not collected (context agent was not invoked for this query)."
    )

    messages = [
        SystemMessage(content=MANAGER_SYSTEM_PROMPT),
        HumanMessage(
            content=f"""
User Question:
{state["question"]}

Transport Agent Output:
{transport_section}

Context Agent Output:
{context_section}

Write a grounded answer for a Singapore commuter.
Use only the provided data.
If information is missing, state that clearly.
"""
        ),
    ]

    response = llm.invoke(messages)
    state["draft_answer"] = response.content if isinstance(response.content, str) else str(response.content)

    state.setdefault("used_agents", []).append("manager_writer")
    state.setdefault("trace", {})["manager_draft"] = state["draft_answer"]
    return state