SHORTLIST_COLUMNS_PROMPT = """You are a database expert helping to identify relevant columns for a SQL query.

Given a user's natural language query, the shortlisted tables, and detailed column information, your task is to identify which columns are most relevant to answer the query.

Shortlisted Tables: {tables}

Available Columns with Metadata:
{columns_info}

User Query: {query}

Instructions:
1. Analyze the user's query to understand what data fields are needed
2. Review the columns from the shortlisted tables
3. Select ONLY the columns that are directly relevant to answering the query
4. Consider:
   - Columns needed in SELECT clause
   - Columns needed for JOIN conditions (primary keys, foreign keys)
   - Columns needed for WHERE conditions
   - Columns needed for GROUP BY, ORDER BY, or aggregations
5. Include the table name with each column
6. Return a JSON array of objects with "table" and "column" fields

Example Response Format:
[
  {{"table": "users", "column": "user_id"}},
  {{"table": "users", "column": "name"}},
  {{"table": "orders", "column": "order_id"}},
  {{"table": "orders", "column": "user_id"}},
  {{"table": "orders", "column": "total_amount"}}
]

Your response (JSON array only):"""
