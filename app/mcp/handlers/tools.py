"""
Tool handlers for the MCP server.

This module provides handlers for MCP tools - functions that perform operations
on the cybernetics ontology data and return results.
"""

import logging
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

# Global reference to the query engine - will be set by the MCPServer
QUERY_ENGINE = None

# Dictionary of available tools
TOOLS: Dict[str, Dict[str, Any]] = {}

def set_query_engine(engine: Any) -> None:
    """
    Set the query engine reference.
    
    Args:
        engine: The CyberneticsQueryEngine instance
    """
    global QUERY_ENGINE
    QUERY_ENGINE = engine
    logger.info("Query engine set for tool handlers")

def _ensure_query_engine() -> bool:
    """Check if the query engine is available."""
    if QUERY_ENGINE is None:
        logger.error("Query engine not set")
        raise RuntimeError("Query engine not available")
    return True

def register_tool(name: str, description: str, handler: Callable, schema: Dict[str, Any]) -> None:
    """
    Register a tool with the MCP server.
    
    Args:
        name: The name of the tool
        description: A description of what the tool does
        handler: The function that implements the tool
        schema: JSON Schema for the tool's parameters
    """
    TOOLS[name] = {
        "name": name,
        "description": description,
        "handler": handler,
        "schema": schema
    }
    logger.debug(f"Registered tool: {name}")

def list_tools_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle a tools/list request.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        List of available tools
    """
    tools_list = []
    
    for name, tool in TOOLS.items():
        tools_list.append({
            "name": name,
            "description": tool["description"],
            "schema": tool["schema"]
        })
    
    return {
        "tools": tools_list
    }

def get_tool_schema_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle a tools/schema request.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        Schema for the requested tool
    """
    tool_name = params.get("name")
    
    if not tool_name:
        return {
            "error": "Tool name is required"
        }
    
    tool = TOOLS.get(tool_name)
    if not tool:
        return {
            "error": f"Tool not found: {tool_name}"
        }
    
    return {
        "name": tool_name,
        "schema": tool["schema"]
    }

def execute_tool_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle a tools/execute request.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        Result of the tool execution
    """
    tool_name = params.get("name")
    tool_params = params.get("params", {})
    
    if not tool_name:
        return {
            "error": "Tool name is required"
        }
    
    tool = TOOLS.get(tool_name)
    if not tool:
        return {
            "error": f"Tool not found: {tool_name}"
        }
    
    try:
        result = tool["handler"](tool_params, transport_id)
        return {
            "name": tool_name,
            "timestamp": datetime.now(UTC).isoformat(),
            "result": result
        }
    except Exception as e:
        logger.exception(f"Error executing tool {tool_name}: {e}")
        return {
            "error": str(e)
        }

# Tool implementations

def search_entities_tool(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Search for entities in the ontology.
    
    Args:
        params: The search parameters
        transport_id: The transport ID
        
    Returns:
        Search results
    """
    _ensure_query_engine()
    
    query = params.get("query", "")
    entity_types = params.get("entity_types")
    limit = int(params.get("limit", 10))
    
    if not query:
        return {"entities": [], "message": "Empty query"}
    
    # Perform the search
    try:
        results = QUERY_ENGINE.search_entities(query, entity_types)
        
        # Limit results
        results = results[:limit]
        
        return {
            "entities": results,
            "query": query,
            "total": len(results)
        }
    except Exception as e:
        logger.exception(f"Error searching entities: {e}")
        return {
            "entities": [],
            "error": str(e),
            "query": query
        }

def analyze_entity_tool(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Analyze an entity's relationships and provide insights.
    
    Args:
        params: The analysis parameters
        transport_id: The transport ID
        
    Returns:
        Entity analysis results
    """
    _ensure_query_engine()
    
    entity_id = params.get("entity_id")
    
    if not entity_id:
        return {"error": "Entity ID is required"}
    
    try:
        # Get entity details
        entity = QUERY_ENGINE.query_entity(entity_id)
        
        # Get connections
        connections = QUERY_ENGINE.find_connections(entity_id, 1)
        
        # Calculate stats
        num_incoming = len(entity.get("incoming", []))
        num_outgoing = len(entity.get("outgoing", []))
        
        # Group connections by relationship type
        relationship_types = {}
        for conn in connections:
            rel_type = conn.get("relationship", {}).get("type")
            if rel_type not in relationship_types:
                relationship_types[rel_type] = 0
            relationship_types[rel_type] += 1
        
        # Get top connected entities
        related_entities = {}
        for conn in connections:
            other_id = conn.get("entity", {}).get("id")
            if other_id not in related_entities:
                related_entities[other_id] = 0
            related_entities[other_id] += 1
        
        top_related = sorted(
            [{"id": k, "count": v} for k, v in related_entities.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:5]
        
        return {
            "entity": {
                "id": entity_id,
                "label": entity.get("attributes", {}).get("label", entity_id),
                "type": entity.get("attributes", {}).get("type", "unknown")
            },
            "stats": {
                "incoming_relationships": num_incoming,
                "outgoing_relationships": num_outgoing,
                "total_relationships": num_incoming + num_outgoing,
                "relationship_types": relationship_types
            },
            "top_connected": top_related
        }
    except Exception as e:
        logger.exception(f"Error analyzing entity: {e}")
        return {"error": str(e)}

def compare_entities_tool(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Compare two entities and find commonalities/differences.
    
    Args:
        params: The comparison parameters
        transport_id: The transport ID
        
    Returns:
        Comparison results
    """
    _ensure_query_engine()
    
    entity1_id = params.get("entity1_id")
    entity2_id = params.get("entity2_id")
    
    if not entity1_id or not entity2_id:
        return {"error": "Both entity IDs are required"}
    
    try:
        # Get entity details
        entity1 = QUERY_ENGINE.query_entity(entity1_id)
        entity2 = QUERY_ENGINE.query_entity(entity2_id)
        
        # Get paths between entities
        paths = QUERY_ENGINE.find_paths(entity1_id, entity2_id, 3)
        
        # Find common relationships
        entity1_rels = set()
        for rel in entity1.get("incoming", []) + entity1.get("outgoing", []):
            entity1_rels.add(rel.get("id"))
        
        entity2_rels = set()
        for rel in entity2.get("incoming", []) + entity2.get("outgoing", []):
            entity2_rels.add(rel.get("id"))
        
        common_rels = entity1_rels.intersection(entity2_rels)
        
        # Get entity properties for comparison
        entity1_props = entity1.get("attributes", {})
        entity2_props = entity2.get("attributes", {})
        
        # Find common and different properties
        common_props = {}
        different_props = {}
        all_keys = set(entity1_props.keys()).union(set(entity2_props.keys()))
        
        for key in all_keys:
            if key in entity1_props and key in entity2_props:
                if entity1_props[key] == entity2_props[key]:
                    common_props[key] = entity1_props[key]
                else:
                    different_props[key] = {
                        "entity1": entity1_props.get(key),
                        "entity2": entity2_props.get(key)
                    }
            elif key in entity1_props:
                different_props[key] = {
                    "entity1": entity1_props.get(key),
                    "entity2": None
                }
            else:
                different_props[key] = {
                    "entity1": None,
                    "entity2": entity2_props.get(key)
                }
        
        return {
            "entities": {
                "entity1": {
                    "id": entity1_id,
                    "label": entity1_props.get("label", entity1_id),
                    "type": entity1_props.get("type", "unknown")
                },
                "entity2": {
                    "id": entity2_id,
                    "label": entity2_props.get("label", entity2_id),
                    "type": entity2_props.get("type", "unknown")
                }
            },
            "paths": {
                "count": len(paths),
                "shortest_path": paths[0] if paths else None
            },
            "common_properties": common_props,
            "different_properties": different_props,
            "common_relationships": len(common_rels)
        }
    except Exception as e:
        logger.exception(f"Error comparing entities: {e}")
        return {"error": str(e)}

def find_central_entities_tool(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Find the most central entities in the ontology.
    
    Args:
        params: The parameters
        transport_id: The transport ID
        
    Returns:
        List of central entities with centrality scores
    """
    _ensure_query_engine()
    
    limit = int(params.get("limit", 10))
    entity_type = params.get("entity_type")
    
    try:
        entities = QUERY_ENGINE.get_central_entities(limit, entity_type)
        
        return {
            "entities": entities,
            "total": len(entities)
        }
    except Exception as e:
        logger.exception(f"Error finding central entities: {e}")
        return {"error": str(e)}

def summarize_ontology_tool(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Provide a summary of the ontology structure.
    
    Args:
        params: The parameters
        transport_id: The transport ID
        
    Returns:
        Ontology summary statistics
    """
    _ensure_query_engine()
    
    try:
        # Get entity and relationship type counts
        entity_types = QUERY_ENGINE.get_entity_types()
        relationship_types = QUERY_ENGINE.get_relationship_types()
        
        # Get overall counts
        total_entities = sum(entity_types.values())
        total_relationships = sum(relationship_types.values())
        
        # Get central entities
        central_entities = QUERY_ENGINE.get_central_entities(5)
        
        return {
            "summary": {
                "total_entities": total_entities,
                "total_relationships": total_relationships,
                "entity_types": entity_types,
                "relationship_types": relationship_types,
                "central_entities": central_entities
            }
        }
    except Exception as e:
        logger.exception(f"Error summarizing ontology: {e}")
        return {"error": str(e)}

# Register tools with schemas
def register_default_tools():
    """Register the default set of tools."""
    
    # Search Entities Tool
    register_tool(
        name="cyberon.tools.search",
        description="Search for entities in the cybernetics ontology",
        handler=search_entities_tool,
        schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "entity_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional filter by entity types"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    )
    
    # Analyze Entity Tool
    register_tool(
        name="cyberon.tools.analyze_entity",
        description="Analyze an entity's relationships and provide insights",
        handler=analyze_entity_tool,
        schema={
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The ID of the entity to analyze"
                }
            },
            "required": ["entity_id"]
        }
    )
    
    # Compare Entities Tool
    register_tool(
        name="cyberon.tools.compare_entities",
        description="Compare two entities and find commonalities/differences",
        handler=compare_entities_tool,
        schema={
            "type": "object",
            "properties": {
                "entity1_id": {
                    "type": "string",
                    "description": "The ID of the first entity to compare"
                },
                "entity2_id": {
                    "type": "string",
                    "description": "The ID of the second entity to compare"
                }
            },
            "required": ["entity1_id", "entity2_id"]
        }
    )
    
    # Central Entities Tool
    register_tool(
        name="cyberon.tools.central_entities",
        description="Find the most central entities in the ontology",
        handler=find_central_entities_tool,
        schema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of entities to return",
                    "default": 10
                },
                "entity_type": {
                    "type": "string",
                    "description": "Optional filter by entity type"
                }
            }
        }
    )
    
    # Summarize Ontology Tool
    register_tool(
        name="cyberon.tools.summarize_ontology",
        description="Provide a summary of the ontology structure",
        handler=summarize_ontology_tool,
        schema={
            "type": "object",
            "properties": {}
        }
    )