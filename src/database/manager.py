"""
Supabase database connection manager.
Provides a unified interface for all database operations using the Singleton pattern.
"""
from typing import Optional, Any, Dict, List
from supabase import create_client, Client
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
    _client: Optional[Client] = None

    def __new__(cls):
        """Singleton instantiation — only one instance is ever created."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initializes the database manager and opens a connection if needed."""
        if self._client is None:
            self.connect()

    def connect(self) -> bool:
        """
        Establishes a connection to Supabase.

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
            self._client = create_client(db_config['url'], db_config['key'])

            logger.info("Supabase connection established successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {str(e)}")
            return False

    def disconnect(self):
        """Closes the current database connection."""
        self._client = None
        logger.info("Supabase connection closed")

    @property
    def client(self) -> Client:
        """
        Returns the active Supabase client.

        Returns:
            Client: Active Supabase client instance.

        Raises:
            ConnectionError: If no connection has been established.
        """
        if self._client is None:
            raise ConnectionError("No active database connection")
        return self._client

    def is_connected(self) -> bool:
        """
        Checks whether a connection is currently active.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._client is not None

    # ============================================
    # GENERIC CRUD OPERATIONS
    # ============================================

    def select(self, table: str, columns: str = "*",
               filters: Optional[Dict[str, Any]] = None,
               order_by: Optional[str] = None,
               limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Executes a SELECT query on a table.

        Args:
            table: Target table name.
            columns: Columns to retrieve (default is all).
            filters: Dictionary of equality filters {column: value}.
            order_by: Column name to sort by.
            limit: Maximum number of records to return.

        Returns:
            List[Dict]: List of matching records.
        """
        try:
            query = self.client.table(table).select(columns)

            if filters:
                for column, value in filters.items():
                    query = query.eq(column, value)

            if order_by:
                query = query.order(order_by)

            if limit:
                query = query.limit(limit)

            response = query.execute()
            return response.data

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
            response = self.client.table(table).insert(data).execute()
            logger.info(f"Record inserted into {table}")
            return response.data[0] if response.data else {}

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
            query = self.client.table(table).update(data)

            for column, value in filters.items():
                query = query.eq(column, value)

            response = query.execute()
            logger.info(f"Record(s) updated in {table}")
            return response.data

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
            query = self.client.table(table).delete()

            for column, value in filters.items():
                query = query.eq(column, value)

            response = query.execute()
            logger.info(f"Record(s) deleted from {table}")
            return response.data

        except Exception as e:
            logger.error(f"DELETE error on {table}: {str(e)}")
            raise

    def execute_rpc(self, function_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Executes a stored PostgreSQL function via RPC.

        Args:
            function_name: Name of the stored function.
            params: Parameters to pass to the function.

        Returns:
            Any: Result returned by the function.
        """
        try:
            response = self.client.rpc(function_name, params or {}).execute()
            return response.data

        except Exception as e:
            logger.error(f"RPC error calling {function_name}: {str(e)}")
            raise

    # ============================================
    # ADVANCED SEARCH OPERATIONS
    # ============================================

    def search(self, table: str, column: str, search_term: str,
               columns: str = "*") -> List[Dict[str, Any]]:
        """
        Performs a case-insensitive text search on a column.

        Args:
            table: Target table name.
            column: Column to search within.
            search_term: Text to search for.
            columns: Columns to return in results.

        Returns:
            List[Dict]: Matching records.
        """
        try:
            response = self.client.table(table).select(columns).ilike(
                column, f"%{search_term}%"
            ).execute()
            return response.data

        except Exception as e:
            logger.error(f"Search error on {table}: {str(e)}")
            raise


# Global database manager instance
db_manager = DatabaseManager()
