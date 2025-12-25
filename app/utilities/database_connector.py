from typing import Any, Dict, List, Optional, Union

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine, Result


class DatabaseConnector:
    """
    A database connector class that works with any database URI.
    Supports operations for retrieving table and column metadata, and executing SQL queries.
    """

    def __init__(self, uri: str):
        """
        Initialize the database connector with a connection URI.

        Args:
            uri: Database connection URI (e.g., 'postgresql://user:pass@host:port/db',
                 'mssql+pyodbc://user:pass@host:port/db?driver=ODBC+Driver+17+for+SQL+Server')
        """
        self.uri = uri
        self.engine: Engine = create_engine(uri)
        self.inspector = inspect(self.engine)

    def get_all_tables(
        self,
        include_tables: Optional[List[str]] = None,
        exclude_tables: Optional[List[str]] = None,
        schema: Optional[str] = None,
    ) -> List[str]:
        """
        Get all table names from the database.

        Args:
            include_tables: List of table names to include. If provided, only these tables are returned.
            exclude_tables: List of table names to exclude. These tables will be filtered out.
            schema: Database schema name (optional, uses default schema if not provided)

        Returns:
            List of table names

        Raises:
            ValueError: If both include_tables and exclude_tables are provided
        """
        if include_tables and exclude_tables:
            raise ValueError("Cannot specify both include_tables and exclude_tables")

        # Get all table names from the database
        all_tables = self.inspector.get_table_names(schema=schema)

        # Apply filters
        if include_tables:
            return [table for table in all_tables if table in include_tables]
        elif exclude_tables:
            return [table for table in all_tables if table not in exclude_tables]
        else:
            return all_tables

    def get_all_columns(
        self,
        include_tables: Optional[List[str]] = None,
        exclude_tables: Optional[List[str]] = None,
        schema: Optional[str] = None,
        as_dataframe: bool = False,
    ) -> Union[Dict[str, List[Dict[str, Any]]], pd.DataFrame]:
        """
        Get all columns from all tables with metadata including primary keys and foreign keys.

        Args:
            include_tables: List of table names to include. If provided, only columns from these tables are returned.
            exclude_tables: List of table names to exclude. Columns from these tables will be filtered out.
            schema: Database schema name (optional, uses default schema if not provided)
            as_dataframe: If True, returns data as a pandas DataFrame, otherwise returns a dictionary

        Returns:
            Dictionary with table names as keys and list of column info dicts as values, or DataFrame
            Each column info dict contains: column_name, type, nullable, default, primary_key, foreign_key,
            foreign_key_reference_table, reference_column

        Raises:
            ValueError: If both include_tables and exclude_tables are provided
        """
        # Get filtered table list
        tables = self.get_all_tables(
            include_tables=include_tables, exclude_tables=exclude_tables, schema=schema
        )

        columns_info = {}
        all_rows = []

        for table_name in tables:
            # Get column information
            columns = self.inspector.get_columns(table_name, schema=schema)

            # Get primary key columns
            pk_constraint = self.inspector.get_pk_constraint(table_name, schema=schema)
            pk_columns = set(pk_constraint.get("constrained_columns", []))

            # Get foreign key information
            fk_constraints = self.inspector.get_foreign_keys(table_name, schema=schema)

            # Create a mapping of column to foreign key info
            fk_map = {}
            for fk in fk_constraints:
                for i, col in enumerate(fk["constrained_columns"]):
                    fk_map[col] = {
                        "referenced_table": fk["referred_table"],
                        "referenced_column": (
                            fk["referred_columns"][i] if i < len(fk["referred_columns"]) else None
                        ),
                    }

            # Build column info list
            table_columns = []
            for col in columns:
                col_name = col["name"]

                column_info = {
                    "table_name": table_name,
                    "column_name": col_name,
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                    "default": col.get("default"),
                    "primary_key": "YES" if col_name in pk_columns else "NO",
                    "foreign_key": "YES" if col_name in fk_map else "NO",
                    "foreign_key_reference_table": fk_map.get(col_name, {}).get("referenced_table"),
                    "reference_column": fk_map.get(col_name, {}).get("referenced_column"),
                }

                table_columns.append(column_info)
                all_rows.append(column_info)

            columns_info[table_name] = table_columns

        if as_dataframe:
            return pd.DataFrame(all_rows)
        else:
            return columns_info

    def execute_sql(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        as_dataframe: bool = False,
        fetch: bool = True,
    ) -> Union[Result, pd.DataFrame, None]:
        """
        Execute a SQL query.

        Args:
            query: SQL query string to execute
            params: Dictionary of parameters for parameterized queries (optional)
            as_dataframe: If True and fetch is True, returns results as pandas DataFrame
            fetch: If True, fetches and returns results. If False, just executes (for INSERT, UPDATE, DELETE)

        Returns:
            - If fetch=True and as_dataframe=True: pandas DataFrame
            - If fetch=True and as_dataframe=False: SQLAlchemy Result object
            - If fetch=False: None

        Examples:
            # SELECT query as DataFrame
            df = db.execute_sql("SELECT * FROM users WHERE age > :age", params={'age': 18}, as_dataframe=True)

            # SELECT query as Result
            result = db.execute_sql("SELECT * FROM users")
            for row in result:
                print(row)

            # INSERT/UPDATE/DELETE (non-fetch)
            db.execute_sql("INSERT INTO users (name, age) VALUES (:name, :age)",
                          params={'name': 'John', 'age': 25}, fetch=False)
        """
        with self.engine.connect() as connection:
            # Use text() for SQL queries with SQLAlchemy 2.0+
            stmt = text(query)

            if fetch:
                # Execute and fetch results
                result = connection.execute(stmt, params or {})

                if as_dataframe:
                    # Convert to DataFrame
                    df = pd.DataFrame(result.fetchall(), columns=result.keys())
                    return df
                else:
                    return result
            else:
                # Execute without fetching (for INSERT, UPDATE, DELETE)
                connection.execute(stmt, params or {})
                connection.commit()
                return None

    def close(self):
        """Close the database connection."""
        self.engine.dispose()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes connection."""
        self.close()
