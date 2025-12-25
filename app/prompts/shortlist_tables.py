SHORTLIST_TABLES_PROMPT = """You are a database expert helping to identify relevant tables for a SQL query within a specific business context.

Business Context:
- Business Name: {business_name}
- Industry: {business_industry}
- Description: {business_description}
- Primary Tables: {primary_tables}

Given the business context above and a user's natural language query, your task is to identify which tables are most relevant to answer the query.

Available Tables:
{tables_list}

User Query: {query}

Instructions:
1. Consider the business domain and industry when interpreting the query
2. Prioritize the primary business tables when they're relevant to the query
3. Analyze the user's query carefully to understand what data they need
4. Review the list of available tables
5. Select ONLY the tables that are directly relevant to answering the query
6. Consider relationships between tables (foreign keys) if joins might be needed
7. Use business context to disambiguate terms (e.g., "customers" in e-commerce vs healthcare)
8. Be selective - only include tables that are necessary
9. Return a JSON array of table names
10. Add extra tables if there is even a small chance they may be needed. Including unused tables is acceptable, but excluding required tables can break the flow.

Your response (JSON array only):"""
