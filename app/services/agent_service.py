from typing import Dict, List

from langgraph.graph import END, START, StateGraph

from app.agent_nodes.agent_state import AgentCustomState
from app.agent_nodes.query_extraction import query_extraction_node


def agent_singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@agent_singleton
class AgentService:
    def __init__(self):
        self.graph = None
        self.build_graph()  # Build graph once at initialization

    def get_graph(self):
        return self.graph

    def build_graph(self):
        if self.graph is not None:
            return self.graph  # Already built, reuse

        workflow = StateGraph(AgentCustomState)

        workflow.add_node("query_extraction_node", query_extraction_node)

        workflow.add_edge(START, "query_extraction_node")
        workflow.add_edge("query_extraction_node", END)

        self.graph = workflow.compile()
        return self.graph

    async def chat_with_agent(self, messages: List[Dict]) -> str:
        # Ensure graph is built (extra safety)
        if self.graph is None:
            self.build_graph()

        response = self.graph.invoke(
            {
                "messages": messages,
                "shortlisted_tables": [],
                "shortlisted_columns": [],
                "generated_sql": "",
                "raw_query": "",
                "transformed_query": "",
            }
        )

        return response
