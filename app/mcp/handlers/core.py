"""
Core request handlers for the MCP server.

This module provides handlers for the basic MCP protocol operations
such as initialization and capability negotiation.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Server capabilities - will be set by the MCPServer on initialization
SERVER_CAPABILITIES = None
SERVER_INSTRUCTIONS = """
CYBERON MCP Server provides access to a cybernetics ontology database. You can:

1. Search for entities in the ontology
2. Retrieve detailed information about entities
3. Find paths between entities
4. Discover connected entities
5. Access ontology data as structured resources
6. Execute tools that analyze and transform the ontology data

Available Query Methods:
- cyberon/search: Search for entities by name or keyword
- cyberon/entity: Get detailed information about a specific entity
- cyberon/paths: Find paths between two entities
- cyberon/connections: Find entities connected to a specific entity
- cyberon/entity_types: Get all entity types in the ontology
- cyberon/relationship_types: Get all relationship types in the ontology

Available Resource Methods:
- resources/list: List available resources in the ontology
- resources/templates/list: List resource templates for dynamic access
- resources/read: Read a specific resource by URI
- resources/subscribe: Subscribe to resource updates
- resources/unsubscribe: Unsubscribe from resource updates

Available Tool Methods:
- tools/list: List available tools
- tools/schema: Get the schema for a specific tool
- tools/execute: Execute a tool with parameters

Resource URIs use the cyberon:// scheme, for example:
- cyberon:///entity/{id}: Access a specific entity
- cyberon:///entity/search?query={query}: Search for entities
- cyberon:///section/{number}: Access a specific section of the ontology
- cyberon:///graph/summary: Get a summary of the ontology graph

Available Tools:
- cyberon.tools.search: Search for entities with advanced options
- cyberon.tools.analyze_entity: Analyze an entity's relationships and provide insights
- cyberon.tools.compare_entities: Compare two entities and find commonalities/differences
- cyberon.tools.central_entities: Find the most central entities in the ontology
- cyberon.tools.summarize_ontology: Provide a summary of the ontology structure

For specific usage details, refer to the method descriptions and tool schemas.
"""

def set_server_capabilities(capabilities: Dict[str, Any]) -> None:
    """
    Set the server capabilities reference.
    
    Args:
        capabilities: The capabilities dictionary from the server
    """
    global SERVER_CAPABILITIES
    SERVER_CAPABILITIES = capabilities

def initialize_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle an initialize request from a client.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        The initialization response with server capabilities
    """
    if not SERVER_CAPABILITIES:
        logger.error("Server capabilities not set")
        raise RuntimeError("Server capabilities not set")
    
    client_name = params.get("client_info", {}).get("name", "Unknown Client")
    client_version = params.get("client_info", {}).get("version", "Unknown Version")
    logger.info(f"Client connected: {client_name} {client_version} via {transport_id}")
    
    # Protocol version negotiation
    client_protocol_version = params.get("protocol_version", "0.0.0")
    server_protocol_version = SERVER_CAPABILITIES["protocol_version"]
    
    # For now, just log the protocol versions - in a real implementation,
    # we would need to handle version compatibility
    logger.info(f"Protocol version negotiation: client={client_protocol_version}, server={server_protocol_version}")
    
    # Prepare the response with server capabilities and instructions
    response = dict(SERVER_CAPABILITIES)
    response["instructions"] = SERVER_INSTRUCTIONS.strip()
    
    return response

def capabilities_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle a capabilities request from a client.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        The server capabilities
    """
    if not SERVER_CAPABILITIES:
        logger.error("Server capabilities not set")
        raise RuntimeError("Server capabilities not set")
    
    logger.debug(f"Capabilities requested by transport {transport_id}")
    return SERVER_CAPABILITIES