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

# Import resource handlers (WP3)
from app.mcp.handlers.resources import (
    list_resources_handler,
    list_resource_templates_handler,
    read_resource_handler,
    resource_subscription_handler,
    resource_unsubscription_handler
)

# Import tool handlers (WP4)
from app.mcp.handlers.tools import (
    register_default_tools,
    list_tools_handler,
    get_tool_schema_handler,
    execute_tool_handler
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
    "get_relationship_types_handler",
    # Resource handlers (WP3)
    "list_resources_handler",
    "list_resource_templates_handler",
    "read_resource_handler",
    "resource_subscription_handler",
    "resource_unsubscription_handler",
    # Tool handlers (WP4)
    "register_default_tools",
    "list_tools_handler",
    "get_tool_schema_handler",
    "execute_tool_handler"
]