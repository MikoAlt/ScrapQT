"""
Centralized database configuration for ScrapQT.
This module provides a single source of truth for database path and reduces syscalls.
"""

import os
import sqlite3
import threading
from typing import Optional, Dict, Any
from contextlib import contextmanager


def get_database_path() -> str:
    """
    Get the database path without reading from any configuration files.
    
    Returns:
        str: Absolute path to the SQLite database file
    """
    # Get the project root directory (where this script is located)
    project_root = os.path.abspath(os.path.dirname(__file__))
    
    # Construct the database path relative to project root
    database_path = os.path.join(project_root, 'data', 'scraped_data.db')
    
    return database_path


def ensure_database_directory() -> str:
    """
    Ensure the database directory exists and return the database path.
    
    Returns:
        str: Absolute path to the SQLite database file
    """
    database_path = get_database_path()
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(database_path), exist_ok=True)
    
    return database_path


# Global constant for use throughout the application
DATABASE_PATH = get_database_path()


class DatabaseConfig:
    """
    Database configuration class with performance optimizations and connection pooling.
    """
    
    def __init__(self, custom_path: Optional[str] = None):
        """
        Initialize database configuration.
        
        Args:
            custom_path: Optional custom database path. If None, uses default.
        """
        if custom_path:
            self.path = os.path.abspath(custom_path)
        else:
            self.path = DATABASE_PATH
            
        # Ensure directory exists only once during initialization
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        
        # Thread-local storage for database connections
        self._local = threading.local()
        self._lock = threading.Lock()
    
    @property 
    def database_path(self) -> str:
        """Get the database path."""
        return self.path
    
    @property
    def data_directory(self) -> str:
        """Get the data directory path."""
        return os.path.dirname(self.path)
    
    def get_connection_string(self) -> str:
        """Get SQLite connection string with optimizations."""
        return f"file:{self.path}?mode=rwc&cache=shared"
    
    @contextmanager
    def get_connection(self):
        """
        Get a database connection with automatic cleanup.
        Uses thread-local storage to reduce connection overhead.
        """
        # Check if we already have a connection for this thread
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.path,
                check_same_thread=False,
                timeout=30.0
            )
            # Enable WAL mode for better concurrent access
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            # Enable foreign key constraints
            self._local.connection.execute("PRAGMA foreign_keys=ON")
            # Optimize for performance
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
            self._local.connection.execute("PRAGMA temp_store=MEMORY")
            self._local.connection.execute("PRAGMA mmap_size=268435456")  # 256MB
            
        try:
            yield self._local.connection
        except Exception as e:
            # Rollback on error
            self._local.connection.rollback()
            raise
    
    def close_connections(self):
        """Close all thread-local connections."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None


# Global database configuration instance
DB_CONFIG = DatabaseConfig()
