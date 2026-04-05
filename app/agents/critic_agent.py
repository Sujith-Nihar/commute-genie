import json
import re
from langchain_core.messages import HumanMessage, SystemMessage

from app.prompts import CRITIC_SYSTEM_PROMPT
from app.services.llm_service import get_llm
from app.state import AgentState


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

    return {
        "approved": True,
        "feedback": "Fallback approval due to parse issue."
    }


def critic_agent_node(state: AgentState) -> AgentState:
    llm = get_llm()

    messages = [
        SystemMessage(content=CRITIC_SYSTEM_PROMPT),
        HumanMessage(
            content=f"""
User Question:
{state["question"]}

Draft Answer:
{state.get("draft_answer")}

Transport Agent Output:
{state.get("transport_result")}

Context Agent Output:
{state.get("context_result")}
"""
        ),
    ]

    response = llm.invoke(messages)
    content = response.content if isinstance(response.content, str) else str(response.content)
    critic_result = _extract_json(content)

    state["critic_result"] = critic_result
    state.setdefault("used_agents", []).append("critic_agent")
    state.setdefault("trace", {})["critic_result"] = critic_result

    if critic_result.get("approved", False):
        state["final_answer"] = state.get("draft_answer", "")
    else:
        feedback = critic_result.get("feedback", "Revision requested.")
        state["final_answer"] = f"{state.get('draft_answer', '')}\n\nCritic note: {feedback}"

    return state