from typing import List, Union

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def format_messages(messages: List[Union[BaseMessage, dict]]) -> str:
    """
    Format messages into a string with "Human:" and "Assistant:" prefixes.

    Args:
        messages: List of LangChain message objects or dictionaries with "role" and "content" keys.
                  Supports HumanMessage, AIMessage, or dicts with role "user"/"human" or "assistant"/"ai".

    Returns:
        Formatted string with messages prefixed by "Human:" or "Assistant:"
    """
    formatted_parts = []
    length = len(messages)

    for message in messages:
        # Handle LangChain message objects
        if isinstance(message, HumanMessage):
            formatted_parts.append(f"Human: {message.content}")
        elif isinstance(message, AIMessage):
            formatted_parts.append(f"Assistant: {message.content}")
        elif isinstance(message, BaseMessage):
            # Generic BaseMessage fallback
            role = getattr(message, "type", "unknown")
            formatted_parts.append(f"{role.capitalize()}: {message.content}")
        # Handle dictionary messages
        elif isinstance(message, dict):
            role = message.get("role", "").lower()
            content = message.get("content", "")

            if role in ("user", "human"):
                formatted_parts.append(f"Human: {content}")
            elif role in ("assistant", "ai"):
                formatted_parts.append(f"Assistant: {content}")
            else:
                # Fallback: use the role as-is if it doesn't match expected values
                formatted_parts.append(f"{role.capitalize()}: {content}")

    header = f"These are the last {length} messages in the conversation:"
    formatted_string = "\n".join(formatted_parts)

    return f"{header}\n{formatted_string}"
