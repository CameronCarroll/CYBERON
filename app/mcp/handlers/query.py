"""
Query engine handlers for the MCP server.

This module provides handlers for interacting with the CyberneticsQueryEngine
through the MCP protocol.
"""

import logging
import json
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Global reference to the query engine - will be set by the MCPServer
QUERY_ENGINE = None
# Global dictionary for sessions - keyed by transport_id
SESSIONS: Dict[str, Dict[str, Any]] = {}

def set_query_engine(engine: Any) -> None:
    """
    Set the query engine reference.
    
    Args:
        engine: The CyberneticsQueryEngine instance
    """
    global QUERY_ENGINE
    QUERY_ENGINE = engine
    logger.info("Query engine set for MCP server")

def _ensure_query_engine() -> bool:
    """Check if the query engine is available."""
    if QUERY_ENGINE is None:
        logger.error("Query engine not set")
        raise RuntimeError("Query engine not available")
    return True

def _get_or_create_session(transport_id: str) -> Dict[str, Any]:
    """
    Get an existing session or create a new one.
    
    Args:
        transport_id: The transport ID
        
    Returns:
        The session data dictionary
    """
    if transport_id not in SESSIONS:
        SESSIONS[transport_id] = {
            "recent_searches": [],
            "recent_entities": [],
            "recent_paths": []
        }
    return SESSIONS[transport_id]

def entity_search_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle an entity search request.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        Search results as dictionary
    """
    _ensure_query_engine()
    session = _get_or_create_session(transport_id)
    
    query = params.get("query", "")
    entity_types = params.get("entity_types")
    limit = int(params.get("limit", 10))
    
    if not query:
        return {"entities": [], "message": "Empty query"}
    
    # Add to recent searches
    if query not in session["recent_searches"]:
        session["recent_searches"].insert(0, query)
        # Keep only the 10 most recent searches
        session["recent_searches"] = session["recent_searches"][:10]
    
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

def entity_info_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle an entity information request.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        Entity details as dictionary
    """
    _ensure_query_engine()
    session = _get_or_create_session(transport_id)
    
    entity_id = params.get("entity_id")
    
    if not entity_id:
        return {"error": "Entity ID is required"}
    
    # Add to recent entities
    if entity_id not in session["recent_entities"]:
        session["recent_entities"].insert(0, entity_id)
        # Keep only the 10 most recent entities
        session["recent_entities"] = session["recent_entities"][:10]
    
    # Get entity details
    try:
        result = QUERY_ENGINE.query_entity(entity_id)
        return result
    except Exception as e:
        logger.exception(f"Error getting entity info: {e}")
        return {"error": str(e)}

def find_paths_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle a find paths request.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        Paths between entities as dictionary
    """
    _ensure_query_engine()
    session = _get_or_create_session(transport_id)
    
    source_id = params.get("source_id")
    target_id = params.get("target_id")
    max_length = int(params.get("max_length", 3))
    
    if not source_id or not target_id:
        return {"error": "Source and target entity IDs are required"}
    
    # Add to recent paths
    path_key = f"{source_id}->{target_id}"
    if path_key not in session["recent_paths"]:
        session["recent_paths"].insert(0, path_key)
        # Keep only the 10 most recent paths
        session["recent_paths"] = session["recent_paths"][:10]
    
    # Find paths
    try:
        paths = QUERY_ENGINE.find_paths(source_id, target_id, max_length)
        
        # Get entity details for source and target
        source = QUERY_ENGINE.query_entity(source_id)
        target = QUERY_ENGINE.query_entity(target_id)
        
        return {
            "paths": paths,
            "source": {
                "id": source_id,
                "label": source.get("attributes", {}).get("label", source_id),
                "type": source.get("attributes", {}).get("type", "unknown")
            },
            "target": {
                "id": target_id,
                "label": target.get("attributes", {}).get("label", target_id),
                "type": target.get("attributes", {}).get("type", "unknown")
            },
            "count": len(paths)
        }
    except Exception as e:
        logger.exception(f"Error finding paths: {e}")
        return {"error": str(e)}

def find_connections_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle a find connections request.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        Connected entities as dictionary
    """
    _ensure_query_engine()
    
    entity_id = params.get("entity_id")
    max_distance = int(params.get("max_distance", 2))
    
    if not entity_id:
        return {"error": "Entity ID is required"}
    
    # Find connections
    try:
        connections = QUERY_ENGINE.find_connections(entity_id, max_distance)
        
        # Get entity details
        entity = QUERY_ENGINE.query_entity(entity_id)
        
        return {
            "connections": connections,
            "entity": {
                "id": entity_id,
                "label": entity.get("attributes", {}).get("label", entity_id),
                "type": entity.get("attributes", {}).get("type", "unknown")
            }
        }
    except Exception as e:
        logger.exception(f"Error finding connections: {e}")
        return {"error": str(e)}

def get_entity_types_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle a get entity types request.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        Entity types as dictionary
    """
    _ensure_query_engine()
    
    try:
        type_counts = QUERY_ENGINE.get_entity_types()
        return {"types": type_counts}
    except Exception as e:
        logger.exception(f"Error getting entity types: {e}")
        return {"error": str(e)}

def get_relationship_types_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle a get relationship types request.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        Relationship types as dictionary
    """
    _ensure_query_engine()
    
    try:
        type_counts = QUERY_ENGINE.get_relationship_types()
        return {"types": type_counts}
    except Exception as e:
        logger.exception(f"Error getting relationship types: {e}")
        return {"error": str(e)}