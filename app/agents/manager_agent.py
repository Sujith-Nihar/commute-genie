from langchain_core.messages import HumanMessage, SystemMessage

from app.prompts import MANAGER_SYSTEM_PROMPT
from app.services.llm_service import get_llm
from app.state import AgentState


def manager_router_node(state: AgentState) -> AgentState:
    question = state["question"].lower()

    use_transport = any(
        k in question for k in [
            "bus", "mrt", "train", "taxi", "traffic", "incident",
            "accident", "eta", "arrival", "disruption", "stop code"
        ]
    )

    use_context = any(
        k in question for k in [
            "rush hour", "holiday", "public holiday", "weather", "today", "crowded"
        ]
    )

    if not use_context:
        use_context = True

    state["manager_plan"] = {
        "use_transport": use_transport,
        "use_context": use_context
    }

    state.setdefault("used_agents", []).append("manager_router")
    state.setdefault("trace", {})["manager_plan"] = state["manager_plan"]
    return state


def manager_writer_node(state: AgentState) -> AgentState:
    llm = get_llm()

    messages = [
        SystemMessage(content=MANAGER_SYSTEM_PROMPT),
        HumanMessage(
            content=f"""
User Question:
{state["question"]}

Transport Agent Output:
{state.get("transport_result")}

Context Agent Output:
{state.get("context_result")}

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