from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from app.agent_nodes.agent_state import AgentCustomState
from app.core.db import get_database
from app.prompts.shortlist_columns import SHORTLIST_COLUMNS_PROMPT
from app.repositories.business_repository import BusinessRepository
from app.repositories.thread_repository import ThreadRepository
from app.schemas.shortlist_columns import ShortlistColumnsResponse
from app.services.business_service import BusinessService
from app.services.thread_service import ThreadService
from app.utilities.llm_utility import llm_utility

shortlist_columns_agent = create_agent(
    model=llm_utility.get_secondary_model(),
    tools=[],
    system_prompt="You are a database expert. Analyze queries and identify relevant columns.",
    name="shortlist_columns_agent",
    response_format=ShortlistColumnsResponse,
)


async def shortlist_columns_node(state: AgentCustomState) -> AgentCustomState:
    """
    Node to shortlist relevant columns based on the user's query and shortlisted tables.

    This node:
    1. Retrieves columns from the shortlisted tables using thread-specific database
    2. Uses an LLM to identify which columns are relevant to the query
    3. Updates the state with the shortlisted columns
    """
    try:
        # Get the transformed query, shortlisted tables, and thread_id from state
        query = state.get("transformed_query", state.get("raw_query", ""))
        shortlisted_tables = state.get("shortlisted_tables", [])
        thread_id = state.get("thread_id")

        if not query:
            raise ValueError("No query found in state")

        if not shortlisted_tables:
            raise ValueError("No shortlisted tables found in state")

        if not thread_id:
            raise ValueError(
                "No thread_id found in state. Thread-based database connection is required."
            )

        # Get thread-specific database connection
        db_client = get_database()
        thread_repository = ThreadRepository(db_client)
        business_repository = BusinessRepository(db_client)
        business_service = BusinessService(business_repository)
        thread_service = ThreadService(thread_repository, business_service)

        columns_info = await thread_service.get_thread_columns(
            thread_id, include_tables=shortlisted_tables
        )
        print(f"Using thread-specific database connection for thread: {thread_id}")

        if not columns_info:
            raise ValueError(f"No columns found for shortlisted tables in thread: {thread_id}")

        # Format columns information for the prompt
        columns_text_parts = []
        for table_name, columns in columns_info.items():
            columns_text_parts.append(f"\nTable: {table_name}")
            for col in columns:
                col_desc = f"  - {col['column_name']} ({col['type']})"
                if col["primary_key"] == "YES":
                    col_desc += " [PRIMARY KEY]"
                if col["foreign_key"] == "YES":
                    col_desc += f" [FOREIGN KEY -> {col['foreign_key_reference_table']}.{col['reference_column']}]"
                if not col["nullable"]:
                    col_desc += " [NOT NULL]"
                columns_text_parts.append(col_desc)

        columns_info_text = "\n".join(columns_text_parts)

        # Get business context
        # First get business_id from thread
        business_id = await thread_service.thread_repository.get_thread_business_id(thread_id)
        if not business_id:
            raise ValueError(
                "Thread business ID not found. This thread may have been created before the business-centric migration. "
                "Please create a new thread using a business ID."
            )

        business_context = await thread_service.business_service.get_business_context(business_id)
        if not business_context:
            raise ValueError(
                f"Business context not found for business ID: {business_id}. "
                "The associated business may have been deleted or is inaccessible."
            )

        # Create the prompt with business context
        prompt = SHORTLIST_COLUMNS_PROMPT.format(
            query=query,
            tables=", ".join(shortlisted_tables),
            columns_info=columns_info_text,
            business_name=business_context.business_name,
            business_industry=business_context.business_industry,
            business_description=business_context.business_description,
            primary_tables=business_context.primary_tables or "Not specified",
        )

        # Invoke the agent
        response = await shortlist_columns_agent.ainvoke(
            {"messages": [HumanMessage(content=prompt)]}
        )

        # Extract structured response
        structured_response: ShortlistColumnsResponse = response["structured_response"]
        shortlisted_columns = [f"{col.table}.{col.column}" for col in structured_response.columns]

        print(f"Shortlisted {len(shortlisted_columns)} columns: {shortlisted_columns}")

        # Update state with shortlisted columns
        return {**state, "shortlisted_columns": shortlisted_columns}

    except Exception as e:
        print(f"Error in shortlist_columns_node: {e}")
        raise e
