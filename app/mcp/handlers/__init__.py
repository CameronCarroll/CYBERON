"""
Request handlers for the MCP server.

This module contains handlers for various MCP requests.
"""

# Import core handlers
from app.mcp.handlers.core import initialize_handler, capabilities_handler

__all__ = ["initialize_handler", "capabilities_handler"]