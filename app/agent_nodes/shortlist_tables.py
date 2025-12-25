from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.agent_nodes.agent_state import AgentCustomState
from app.core.db import get_database
from app.prompts.shortlist_tables import SHORTLIST_TABLES_PROMPT
from app.repositories.thread_repository import ThreadRepository
from app.schemas.shortlist_tables import ShortlistTablesResponse
from app.services.thread_service import ThreadService
from app.utilities.llm_utility import llm_utility

shortlist_tables_agent = create_agent(
    model=llm_utility.get_secondary_model(),
    tools=[],
    system_prompt="You are a database expert. Analyze queries and identify relevant tables.",
    name="shortlist_tables_agent",
    response_format=ShortlistTablesResponse,
)


async def shortlist_tables_node(state: AgentCustomState) -> Command:
    """
    Node to shortlist relevant tables based on the user's query.

    This node:
    1. Retrieves all available tables from the thread-specific database
    2. Uses an LLM to identify which tables are relevant to the query
    3. Updates the state with the shortlisted tables
    """
    try:
        # Get the transformed query and thread_id from state
        query = state.get("transformed_query", state.get("raw_query", ""))
        thread_id = state.get("thread_id")

        if not query:
            raise ValueError("No query found in state")

        if not thread_id:
            raise ValueError(
                "No thread_id found in state. Thread-based database connection is required."
            )

        # Get thread-specific database connection
        db_client = get_database()
        thread_repository = ThreadRepository(db_client)
        thread_service = ThreadService(thread_repository)

        all_tables = await thread_service.get_thread_tables(thread_id)
        print(f"Using thread-specific database connection for thread: {thread_id}")

        if not all_tables:
            raise ValueError(f"No tables found in database for thread: {thread_id}")

        # Format tables list for the prompt
        tables_list = "\n".join([f"- {table}" for table in all_tables])

        # Create the prompt
        prompt = SHORTLIST_TABLES_PROMPT.format(query=query, tables_list=tables_list)

        # Invoke the agent
        response = await shortlist_tables_agent.ainvoke(
            {"messages": [HumanMessage(content=prompt)]}
        )

        # Extract structured response
        structured_response: ShortlistTablesResponse = response["structured_response"]
        shortlisted_tables = structured_response.tables

        print(f"Shortlisted {len(shortlisted_tables)} tables: {shortlisted_tables}")

        # Update state with shortlisted tables
        return Command(
            goto="shortlist_columns_node", update={"shortlisted_tables": shortlisted_tables}
        )

    except Exception as e:
        print(f"Error in shortlist_tables_node: {e}")
        raise e
