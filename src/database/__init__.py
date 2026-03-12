"""
Database package.
Re-exports DatabaseManager and db_manager from the manager module.
"""
from src.database.manager import DatabaseManager, db_manager

__all__ = ['DatabaseManager', 'db_manager']
