"""
PostgreSQL database connection manager.
Provides a unified interface for all database operations using the Singleton pattern.
"""
from typing import Optional, Any, Dict, List
import psycopg2
import psycopg2.extras
from src.config import config
import logging

# Configure module-level logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Centralized database manager.
    Implements the Singleton pattern to guarantee a single connection instance.
    """

    _instance: Optional['DatabaseManager'] = None
    _conn = None

    def __new__(cls):
        """Singleton instantiation — only one instance is ever created."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initializes the database manager and opens a connection if needed."""
        if self._conn is None:
            self.connect()

    def connect(self) -> bool:
        """
        Establishes a connection to PostgreSQL.

        Returns:
            bool: True if the connection was successful, False otherwise.
        """
        try:
            # Validate configuration before connecting
            is_valid, errors = config.validate()
            if not is_valid:
                for error in errors:
                    logger.error(f"Configuration error: {error}")
                return False

            db_config = config.get_database_config()
            self._conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                dbname=db_config['dbname'],
                user=db_config['user'],
                password=db_config['password'],
                cursor_factory=psycopg2.extras.RealDictCursor,
            )
            self._conn.autocommit = True

            logger.info("PostgreSQL connection established successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            return False

    def disconnect(self):
        """Closes the current database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
        logger.info("PostgreSQL connection closed")

    @property
    def connection(self):
        """
        Returns the active database connection.

        Returns:
            Connection: Active psycopg2 connection instance.

        Raises:
            ConnectionError: If no connection has been established.
        """
        if self._conn is None or self._conn.closed:
            raise ConnectionError("No active database connection")
        return self._conn

    def is_connected(self) -> bool:
        """
        Checks whether a connection is currently active.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._conn is not None and not self._conn.closed

    # ============================================
    # INTERNAL HELPERS
    # ============================================

    @staticmethod
    def _build_where(filters: Optional[Dict[str, Any]]) -> tuple:
        """Builds a WHERE clause from a filters dictionary.

        Returns:
            tuple[str, tuple]: (clause, params) — clause starts with ' WHERE '
                               or is empty; params are the bound values.
        """
        if not filters:
            return "", ()
        conditions = [f"{col} = %s" for col in filters]
        return " WHERE " + " AND ".join(conditions), tuple(filters.values())

    def _execute(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Executes a query and returns all resulting rows as dicts."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    return cursor.fetchall()
                return []
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            raise

    def _execute_one(self, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """Executes a query and returns a single row as a dict."""
        rows = self._execute(query, params)
        return rows[0] if rows else {}

    # ============================================
    # GENERIC CRUD OPERATIONS
    # ============================================

    def select(self, table: str, columns: str = "*",
               filters: Optional[Dict[str, Any]] = None,
               order_by: Optional[str] = None,
               limit: Optional[int] = None,
               joins: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Executes a SELECT query on a table.

        Args:
            table: Target table name.
            columns: Columns to retrieve (default is all).
            filters: Dictionary of equality filters {column: value}.
            order_by: Column name to sort by.
            limit: Maximum number of records to return.
            joins: Optional list of JOIN clauses, e.g. ["LEFT JOIN members ON ..."].

        Returns:
            List[Dict]: List of matching records.
        """
        try:
            query = f"SELECT {columns} FROM {table}"
            if joins:
                for join_clause in joins:
                    query += f" {join_clause}"
            where_clause, params = self._build_where(filters)
            query += where_clause
            if order_by:
                query += f" ORDER BY {order_by}"
            if limit:
                query += f" LIMIT {limit}"

            return self._execute(query, params if params else None)

        except Exception as e:
            logger.error(f"SELECT error on {table}: {str(e)}")
            raise

    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserts a record into a table.

        Args:
            table: Target table name.
            data: Dictionary of field values to insert.

        Returns:
            Dict: The inserted record including its generated ID.
        """
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["%s"] * len(data))
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING *"

            row = self._execute_one(query, tuple(data.values()))
            logger.info(f"Record inserted into {table}")
            return row

        except Exception as e:
            logger.error(f"INSERT error on {table}: {str(e)}")
            raise

    def update(self, table: str, data: Dict[str, Any],
               filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Updates records in a table.

        Args:
            table: Target table name.
            data: Dictionary of fields to update.
            filters: Dictionary of equality filters {column: value}.

        Returns:
            List[Dict]: Updated records.
        """
        try:
            set_clause = ", ".join([f"{col} = %s" for col in data])
            where_clause, where_params = self._build_where(filters)
            query = f"UPDATE {table} SET {set_clause}{where_clause} RETURNING *"
            params = tuple(data.values()) + where_params

            rows = self._execute(query, params)
            logger.info(f"Record(s) updated in {table}")
            return rows

        except Exception as e:
            logger.error(f"UPDATE error on {table}: {str(e)}")
            raise

    def delete(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Deletes records from a table.

        Args:
            table: Target table name.
            filters: Dictionary of equality filters {column: value}.

        Returns:
            List[Dict]: Deleted records.
        """
        try:
            where_clause, params = self._build_where(filters)
            query = f"DELETE FROM {table}{where_clause} RETURNING *"

            rows = self._execute(query, params)
            logger.info(f"Record(s) deleted from {table}")
            return rows

        except Exception as e:
            logger.error(f"DELETE error on {table}: {str(e)}")
            raise

    def execute_rpc(self, function_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Executes a stored PostgreSQL function.

        Args:
            function_name: Name of the stored function.
            params: Parameters to pass to the function.

        Returns:
            Any: Result returned by the function.
        """
        try:
            if params:
                placeholders = ", ".join(["%s"] * len(params))
                query = f"SELECT * FROM {function_name}({placeholders})"
                return self._execute(query, tuple(params.values()))
            else:
                query = f"SELECT * FROM {function_name}()"
                return self._execute(query)

        except Exception as e:
            logger.error(f"RPC error calling {function_name}: {str(e)}")
            raise

    def select_range(self, table: str, column: str, start: str, end: str,
                     columns: str = "*",
                     filters: Optional[Dict[str, Any]] = None,
                     order_by: Optional[str] = None,
                     joins: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Executes a SELECT query filtering a column between two values (inclusive).

        Args:
            table: Target table name.
            column: Column to apply the range filter on.
            start: Lower bound value (inclusive).
            end: Upper bound value (inclusive).
            columns: Columns to retrieve (default is all).
            filters: Optional additional equality filters {column: value}.
            order_by: Column name to sort by.
            joins: Optional list of JOIN clauses.

        Returns:
            List[Dict]: List of matching records.
        """
        try:
            query = f"SELECT {columns} FROM {table}"
            if joins:
                for join_clause in joins:
                    query += f" {join_clause}"
            query += f" WHERE {column} >= %s AND {column} <= %s"
            params = [start, end]

            if filters:
                for col, value in filters.items():
                    query += f" AND {col} = %s"
                    params.append(value)

            if order_by:
                query += f" ORDER BY {order_by}"

            return self._execute(query, tuple(params))

        except Exception as e:
            logger.error(f"SELECT range error on {table}: {str(e)}")
            raise

    # ============================================
    # ADVANCED SEARCH OPERATIONS
    # ============================================

    def search(self, table: str, column: str, search_term: str,
               columns: str = "*",
               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Performs a case-insensitive text search on a column.

        Args:
            table: Target table name.
            column: Column to search within (can be an expression, e.g. "first_name || ' ' || last_name").
            search_term: Text to search for.
            columns: Columns to return in results.
            filters: Optional equality filters applied alongside the ILIKE
                     condition, e.g. {'is_active': True}.

        Returns:
            List[Dict]: Matching records.
        """
        try:
            query = f"SELECT {columns} FROM {table} WHERE {column} ILIKE %s"
            params = [f"%{search_term}%"]

            if filters:
                for col, value in filters.items():
                    query += f" AND {col} = %s"
                    params.append(value)

            return self._execute(query, tuple(params))

        except Exception as e:
            logger.error(f"Search error on {table}: {str(e)}")
            raise


# Global database manager instance
db_manager = DatabaseManager()
