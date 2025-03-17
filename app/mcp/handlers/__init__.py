"""
Request handlers for the MCP server.

This module contains handlers for various MCP requests.
"""

# Import core handlers
from app.mcp.handlers.core import initialize_handler, capabilities_handler

# Import query handlers (WP2)
from app.mcp.handlers.query import (
    set_query_engine,
    entity_search_handler,
    entity_info_handler,
    find_paths_handler,
    find_connections_handler,
    get_entity_types_handler,
    get_relationship_types_handler
)

__all__ = [
    "initialize_handler", 
    "capabilities_handler",
    # Query engine handlers (WP2)
    "set_query_engine",
    "entity_search_handler",
    "entity_info_handler",
    "find_paths_handler",
    "find_connections_handler",
    "get_entity_types_handler",
    "get_relationship_types_handler"
]