from typing import Optional

from langchain.agents import AgentState


class AgentCustomState(AgentState):
    raw_query: str
    transformed_query: str
    shortlisted_tables: list[str]
    shortlisted_columns: list[str]
    generated_sql: str
    thread_id: Optional[str] = None  # Thread ID for database connection
