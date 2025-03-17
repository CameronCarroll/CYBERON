"""
MCP Server implementation for CYBERON.

This module provides the core server implementation for the Model Context Protocol.
"""

import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Callable, Tuple

from jsonschema import validate, ValidationError
from app.mcp.transports import StdioTransport, Transport
from app.mcp.handlers import (
    initialize_handler, 
    capabilities_handler,
    # Work Package 2 - Query engine handlers
    set_query_engine,
    entity_search_handler,
    entity_info_handler,
    find_paths_handler,
    find_connections_handler,
    get_entity_types_handler,
    get_relationship_types_handler
)

# Work Package 3 - Resource handlers
from app.mcp.handlers.resources import (
    list_resources_handler,
    list_resource_templates_handler,
    read_resource_handler,
    resource_subscription_handler,
    resource_unsubscription_handler
)

# Work Package 4 - Tool handlers
from app.mcp.handlers.tools import (
    list_tools_handler,
    get_tool_schema_handler,
    execute_tool_handler,
    register_default_tools
)

# Work Package 6 - Prompt handlers
from app.mcp.handlers.prompts import (
    list_prompts_handler,
    get_prompt_handler,
    register_default_prompts
)

logger = logging.getLogger(__name__)

class MCPServer:
    """
    Model Context Protocol server implementation.
    
    This server handles MCP protocol messages, negotiates capabilities,
    and manages transport layers to communicate with clients.
    """
    
    PROTOCOL_VERSION = "0.5.0"
    
    def __init__(self):
        """Initialize the MCP server."""
        self.transports: Dict[str, Transport] = {}
        self.capabilities: Dict[str, Any] = {
            "protocol_version": self.PROTOCOL_VERSION,
            "server_info": {
                "name": "CYBERON MCP Server",
                "version": "0.1.0",
                "vendor": "CYBERON Project"
            },
            "supports": {
                "resources": True,   # Implemented in Work Package 3
                "tools": True,       # Implemented in Work Package 4
                "prompts": True      # Implemented in Work Package 6
            }
        }
        self.request_handlers: Dict[str, Callable] = {}
        self.query_engine = None
        
        # Initialize handlers
        from app.mcp.handlers.core import set_server_capabilities
        
        # Set server capabilities for handlers
        set_server_capabilities(self.capabilities)
        
        # Register core request handlers
        self._register_core_handlers()
        
        logger.info(f"MCP Server initialized with protocol version {self.PROTOCOL_VERSION}")
    
    def _register_core_handlers(self) -> None:
        """Register core request handlers for the MCP protocol."""
        # Core protocol handlers
        self.register_handler("initialize", initialize_handler)
        self.register_handler("server/capabilities", capabilities_handler)
        
        # Work Package 2 - Query engine handlers
        self.register_handler("cyberon/search", entity_search_handler)
        self.register_handler("cyberon/entity", entity_info_handler)
        self.register_handler("cyberon/paths", find_paths_handler)
        self.register_handler("cyberon/connections", find_connections_handler)
        self.register_handler("cyberon/entity_types", get_entity_types_handler)
        self.register_handler("cyberon/relationship_types", get_relationship_types_handler)
        
        # Work Package 3 - Resource handlers
        self.register_handler("resources/list", list_resources_handler)
        self.register_handler("resources/templates/list", list_resource_templates_handler)
        self.register_handler("resources/read", read_resource_handler)
        self.register_handler("resources/subscribe", resource_subscription_handler)
        self.register_handler("resources/unsubscribe", resource_unsubscription_handler)
        
        # Work Package 4 - Tool handlers
        self.register_handler("tools/list", list_tools_handler)
        self.register_handler("tools/schema", get_tool_schema_handler)
        self.register_handler("tools/execute", execute_tool_handler)
        
        # Register default tools
        register_default_tools()
        
        # Work Package 6 - Prompt handlers
        self.register_handler("prompts/list", list_prompts_handler)
        self.register_handler("prompts/get", get_prompt_handler)
        
        # Register default prompts
        register_default_prompts()
    
    def register_handler(self, method: str, handler: Callable) -> None:
        """
        Register a request handler for a specific method.
        
        Args:
            method: The method name to handle
            handler: The function to call when this method is requested
        """
        self.request_handlers[method] = handler
        logger.debug(f"Registered handler for method: {method}")
    
    def register_transport(self, transport: Transport) -> str:
        """
        Register a transport with the server.
        
        Args:
            transport: The transport instance to register
            
        Returns:
            The transport ID
        """
        transport_id = str(uuid.uuid4())
        self.transports[transport_id] = transport
        transport.set_message_handler(self.handle_message)
        logger.info(f"Registered transport {transport_id} of type {type(transport).__name__}")
        return transport_id
    
    def create_stdio_transport(self) -> str:
        """
        Create and register a STDIO transport.
        
        Returns:
            The transport ID
        """
        transport = StdioTransport()
        return self.register_transport(transport)
    
    def set_query_engine(self, engine) -> None:
        """
        Set the query engine for the MCP server.
        
        Args:
            engine: The CyberneticsQueryEngine instance
        """
        self.query_engine = engine
        
        # Set the query engine for all handlers that need it
        from app.mcp.handlers.query import set_query_engine as set_query_engine_for_query
        from app.mcp.handlers.resources import set_query_engine as set_query_engine_for_resources
        from app.mcp.handlers.tools import set_query_engine as set_query_engine_for_tools
        from app.mcp.handlers.prompts import set_query_engine as set_query_engine_for_prompts
        
        set_query_engine_for_query(engine)
        set_query_engine_for_resources(engine)
        set_query_engine_for_tools(engine)
        set_query_engine_for_prompts(engine)
        
        logger.info("Query engine set for MCP server")
    
    def handle_message(self, message: str, transport_id: str) -> Optional[str]:
        """
        Handle an incoming message from a transport.
        
        Args:
            message: The raw message string
            transport_id: The ID of the transport that received the message
            
        Returns:
            The response message or None if no response is needed
        """
        try:
            request = json.loads(message)
            
            # Check if this is a JSON-RPC 2.0 request
            if "jsonrpc" not in request or request["jsonrpc"] != "2.0":
                return self._create_error_response(
                    request.get("id"), 
                    -32600, 
                    "Invalid Request", 
                    "Request does not follow JSON-RPC 2.0 specification"
                )
            
            # Handle the request
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if not method:
                return self._create_error_response(
                    request_id, 
                    -32600, 
                    "Invalid Request", 
                    "Method not specified"
                )
            
            # Find and execute the appropriate handler
            handler = self.request_handlers.get(method)
            if not handler:
                return self._create_error_response(
                    request_id, 
                    -32601, 
                    "Method not found", 
                    f"No handler registered for method: {method}"
                )
            
            # Execute the handler and get the result
            try:
                result = handler(params, transport_id)
                
                # Only return a response for requests, not for notifications
                if request_id is not None:
                    return json.dumps({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": result
                    })
                return None
                
            except ValidationError as e:
                return self._create_error_response(
                    request_id, 
                    -32602, 
                    "Invalid params", 
                    str(e)
                )
            except Exception as e:
                logger.exception(f"Error handling method {method}")
                return self._create_error_response(
                    request_id, 
                    -32603, 
                    "Internal error", 
                    str(e)
                )
                
        except json.JSONDecodeError:
            return self._create_error_response(
                None,
                -32700, 
                "Parse error", 
                "Invalid JSON"
            )
    
    def _create_error_response(self, request_id: Any, code: int, message: str, data: Optional[str] = None) -> str:
        """
        Create a JSON-RPC 2.0 error response.
        
        Args:
            request_id: The ID from the request (or None)
            code: The error code
            message: The error message
            data: Optional additional error data
            
        Returns:
            The JSON-encoded error response
        """
        error = {
            "code": code,
            "message": message
        }
        
        if data:
            error["data"] = data
            
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error
        }
        
        return json.dumps(response)
    
    def start(self) -> None:
        """
        Start the MCP server and all registered transports.
        """
        if not self.transports:
            raise RuntimeError("No transports registered with the server")
        
        logger.info("Starting MCP server")
        
        # Start all transports
        for transport_id, transport in self.transports.items():
            logger.info(f"Starting transport {transport_id}")
            transport.start()
    
    def stop(self) -> None:
        """
        Stop the MCP server and all registered transports.
        """
        logger.info("Stopping MCP server")
        
        # Stop all transports
        for transport_id, transport in self.transports.items():
            logger.info(f"Stopping transport {transport_id}")
            transport.stop()