from langchain.agents import AgentState


class AgentCustomState(AgentState):
    raw_query: str
    transformed_query: str
    shortlisted_tables: list[str]
    shortlisted_columns: list[str]
    generated_sql: str
