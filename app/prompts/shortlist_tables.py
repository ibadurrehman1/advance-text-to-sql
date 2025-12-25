SHORTLIST_TABLES_PROMPT = """You are a database expert helping to identify relevant tables for a SQL query.

Given a user's natural language query and a list of available database tables, your task is to identify which tables are most relevant to answer the query.

Available Tables:
{tables_list}

User Query: {query}

Instructions:
1. Analyze the user's query carefully to understand what data they need
2. Review the list of available tables
3. Select ONLY the tables that are directly relevant to answering the query
4. Consider relationships between tables (foreign keys) if joins might be needed
5. Be selective - only include tables that are necessary
6. Return a JSON array of table names

Example Response Format:
["users", "orders", "products"]

Your response (JSON array only):"""
