from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command

from app.agent_nodes.agent_state import AgentCustomState
from app.helpers.llm_helper import format_messages
from app.prompts.query_extraction import query_extraction_prompt
from app.schemas.query_extraction import ExtractedQuery
from app.utilities.llm_utility import llm_utility

query_extraction_agent = create_agent(
    model=llm_utility.get_secondary_model(),
    tools=[],
    system_prompt=query_extraction_prompt,
    name="query_extraction_agent",
    response_format=ExtractedQuery,
)


async def query_extraction_node(state: AgentCustomState) -> Command:

    last_10_messages = format_messages(state["messages"][-10:])

    response = await query_extraction_agent.ainvoke(
        {"messages": [HumanMessage(content=last_10_messages)]}
    )
    structured_response: ExtractedQuery = response["structured_response"]

    if structured_response.off_topic:
        return Command(
            goto="end", update={"messages": AIMessage(content=structured_response.off_topic_reply)}
        )

    return Command(
        goto="shortlist_tables_node",
        update={
            "transformed_query": structured_response.extracted_query,
            "raw_query": state["messages"][-1].content,
        },
    )
