from app.agent_nodes.agent_state import AgentCustomState


def query_transformation_node(state: AgentCustomState) -> AgentCustomState:

    state["raw_query"] = state["messages"][-1].content
    state["transformed_query"] = state["raw_query"]
    state["shortlisted_tables"] = []
    state["shortlisted_columns"] = []
    state["generated_sql"] = ""
    return state
