SHORTLIST_COLUMNS_PROMPT = """You are a database expert helping to identify relevant columns for a SQL query within a specific business context.

Business Context:
- Business Name: {business_name}
- Industry: {business_industry}
- Description: {business_description}
- Primary Tables: {primary_tables}

Given the business context above, a user's natural language query, the shortlisted tables, and detailed column information,
your task is to identify which columns are most relevant to answer the query.

Shortlisted Tables: {tables}

Available Columns with Metadata:
{columns_info}

User Query: {query}

Instructions:
1. Consider the business domain and industry when interpreting column meanings
2. Analyze the user's query to understand what data fields are needed
3. Review the columns from the shortlisted tables
4. Select ONLY the columns that are directly relevant to answering the query
5. Consider:
   - Columns needed in SELECT clause
   - Columns needed for JOIN conditions (primary keys, foreign keys)
   - Columns needed for WHERE conditions
   - Columns needed for GROUP BY, ORDER BY, or aggregations
6. Use business context to understand column purposes (e.g., "amount" could be price, salary, etc.)
7. Include the table name with each column
8. Return a JSON array of objects with "table" and "column" fields
9. Add extra columns if there is even a small chance they may be needed. Including unused columns is acceptable, but excluding required columns can break the flow.

Example Response Format:
[
  {{"table": "users", "column": "user_id"}},
  {{"table": "users", "column": "name"}},
  {{"table": "orders", "column": "order_id"}},
  {{"table": "orders", "column": "user_id"}},
  {{"table": "orders", "column": "total_amount"}}
]

Your response (JSON array only):"""
