from langgraph.graph import END, StateGraph

from app.agents.context_agent import context_agent_node
from app.agents.critic_agent import critic_agent_node
from app.agents.manager_agent import manager_router_node, manager_writer_node
from app.agents.transport_agent import transport_agent_node
from app.agents.trip_planner_agent import trip_planner_node
from app.state import AgentState


def route_after_manager(state: AgentState) -> str:
    plan = state.get("manager_plan", {})

    # Trip planner takes priority — it handles its own geocoding, routing,
    # real-time signals, scoring, and draft writing internally.
    if plan.get("use_trip_planner", False):
        return "trip_planner"

    use_transport = plan.get("use_transport", False)
    use_context = plan.get("use_context", False)

    if use_transport and use_context:
        return "transport"
    if use_transport:
        return "transport_only"
    if use_context:
        return "context_only"
    return "write"


def route_after_transport(state: AgentState) -> str:
    plan = state.get("manager_plan", {})
    return "context" if plan.get("use_context", False) else "write"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("manager_router", manager_router_node)
    graph.add_node("trip_planner", trip_planner_node)
    graph.add_node("transport_agent", transport_agent_node)
    graph.add_node("context_agent", context_agent_node)
    graph.add_node("manager_writer", manager_writer_node)
    graph.add_node("critic_agent", critic_agent_node)

    graph.set_entry_point("manager_router")

    graph.add_conditional_edges(
        "manager_router",
        route_after_manager,
        {
            "trip_planner": "trip_planner",
            "transport": "transport_agent",
            "transport_only": "transport_agent",
            "context_only": "context_agent",
            "write": "manager_writer",
        },
    )

    # Trip planner writes its own draft; go straight to manager_writer
    # (which will detect trip_result and pass-through) then to critic.
    graph.add_edge("trip_planner", "manager_writer")

    graph.add_conditional_edges(
        "transport_agent",
        route_after_transport,
        {
            "context": "context_agent",
            "write": "manager_writer",
        },
    )

    graph.add_edge("context_agent", "manager_writer")
    graph.add_edge("manager_writer", "critic_agent")
    graph.add_edge("critic_agent", END)

    return graph.compile()


commutegenie_graph = build_graph()