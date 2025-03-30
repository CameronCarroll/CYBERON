"""
Resource handlers for the MCP server.

This module provides handlers for interacting with resources through the MCP protocol.
Resources represent accessible data from the CyberneticsQueryEngine.
"""

import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)

# Global reference to the query engine - will be set by the MCPServer
QUERY_ENGINE = None

# Ontology resource types
RESOURCE_TYPES = {
    "entity": {
        "description": "An entity in the cybernetics ontology",
        "name": "Entity",
        "mime_type": "application/json"
    },
    "relationship": {
        "description": "A relationship between entities in the cybernetics ontology",
        "name": "Relationship",
        "mime_type": "application/json"
    },
    "section": {
        "description": "A section of the structured ontology",
        "name": "Section",
        "mime_type": "application/json"
    },
    "entity_type": {
        "description": "A type of entity in the cybernetics ontology",
        "name": "Entity Type",
        "mime_type": "application/json"
    },
    "relationship_type": {
        "description": "A type of relationship in the cybernetics ontology",
        "name": "Relationship Type",
        "mime_type": "application/json"
    },
    "graph_summary": {
        "description": "A summary of the ontology graph structure",
        "name": "Graph Summary",
        "mime_type": "application/json"
    }
}

def set_query_engine(engine: Any) -> None:
    """
    Set the query engine reference.
    
    Args:
        engine: The CyberneticsQueryEngine instance
    """
    global QUERY_ENGINE
    QUERY_ENGINE = engine

def _ensure_query_engine() -> bool:
    """Check if the query engine is available."""
    if QUERY_ENGINE is None:
        logger.error("Query engine not set")
        raise RuntimeError("Query engine not available")
    return True

def list_resources_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle a resources/list request.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        List of available resources
    """
    _ensure_query_engine()
    
    cursor = params.get("cursor")
    resources = []
    
    # Entity types as resources
    entity_types = QUERY_ENGINE.get_entity_types()
    for entity_type, count in entity_types.items():
        resources.append({
            "name": f"Entity Type: {entity_type}",
            "uri": f"cyberon:///entity_type/{entity_type}",
            "description": f"Information about the '{entity_type}' entity type ({count} entities)",
            "mimeType": "application/json"
        })
    
    # Relationship types as resources
    relationship_types = QUERY_ENGINE.get_relationship_types()
    for rel_type, count in relationship_types.items():
        resources.append({
            "name": f"Relationship Type: {rel_type}",
            "uri": f"cyberon:///relationship_type/{rel_type}",
            "description": f"Information about the '{rel_type}' relationship type ({count} relationships)",
            "mimeType": "application/json"
        })
    
    # Add ontology sections as resources
    for section_num, section_data in QUERY_ENGINE.structured_ontology.items():
        section_title = section_data.get("title", f"Section {section_num}")
        resources.append({
            "name": f"Section {section_num}: {section_title}",
            "uri": f"cyberon:///section/{section_num}",
            "description": f"Content of section {section_num}: {section_title}",
            "mimeType": "application/json"
        })
    
    # Add resource templates
    resources.append({
        "name": "Entity",
        "uri": "cyberon:///entity/{id}",
        "description": "Detailed information about a specific entity by ID",
        "mimeType": "application/json"
    })
    
    resources.append({
        "name": "Entity Search",
        "uri": "cyberon:///entity/search?query={query}",
        "description": "Search for entities by keyword",
        "mimeType": "application/json"
    })
    
    resources.append({
        "name": "Relationship",
        "uri": "cyberon:///relationship/{id}",
        "description": "Detailed information about a specific relationship by ID",
        "mimeType": "application/json"
    })
    
    resources.append({
        "name": "Graph Summary",
        "uri": "cyberon:///graph/summary",
        "description": "Summary information about the ontology graph",
        "mimeType": "application/json"
    })
    
    # Add some central entities as resources for easy access
    central_entities = QUERY_ENGINE.get_central_entities(5)
    for entity in central_entities:
        resources.append({
            "name": f"Entity: {entity['label']}",
            "uri": f"cyberon:///entity/{entity['id']}",
            "description": f"Information about {entity['label']} (centrality: {entity['centrality']:.2f})",
            "mimeType": "application/json"
        })
    
    return {
        "resources": resources
    }

def list_resource_templates_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle a resources/templates/list request.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        List of available resource templates
    """
    _ensure_query_engine()
    
    cursor = params.get("cursor")
    templates = []
    
    # Entity template
    templates.append({
        "name": "Entity",
        "uriTemplate": "cyberon:///entity/{id}",
        "description": "Detailed information about a specific entity by ID",
        "mimeType": "application/json"
    })
    
    # Entity search template
    templates.append({
        "name": "Entity Search",
        "uriTemplate": "cyberon:///entity/search{?query,type}",
        "description": "Search for entities by keyword and optionally filter by type"
    })
    
    # Relationship template
    templates.append({
        "name": "Relationship",
        "uriTemplate": "cyberon:///relationship/{id}",
        "description": "Detailed information about a specific relationship by ID",
        "mimeType": "application/json"
    })
    
    # Paths template
    templates.append({
        "name": "Paths",
        "uriTemplate": "cyberon:///paths{?source,target,max_length}",
        "description": "Find paths between two entities"
    })
    
    # Connections template
    templates.append({
        "name": "Connections",
        "uriTemplate": "cyberon:///connections/{entity_id}{?max_distance}",
        "description": "Find connections to a specific entity"
    })
    
    # Section template
    templates.append({
        "name": "Section",
        "uriTemplate": "cyberon:///section/{number}",
        "description": "Content of a specific section of the structured ontology"
    })
    
    # Subsection template
    templates.append({
        "name": "Subsection",
        "uriTemplate": "cyberon:///section/{number}/{subsection}",
        "description": "Content of a specific subsection within a section"
    })
    
    return {
        "resourceTemplates": templates
    }

def read_resource_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle a resources/read request.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        Content of the requested resource
    """
    _ensure_query_engine()
    
    uri = params.get("uri")
    if not uri:
        raise ValueError("URI is required")
    
    # Parse the URI
    parsed_uri = urlparse(uri)
    
    # Check schema is correct
    if parsed_uri.scheme != "cyberon":
        raise ValueError(f"Unsupported URI scheme: {parsed_uri.scheme}")
    
    # Remove leading slash if present
    path = parsed_uri.path
    if path.startswith('/'):
        path = path[1:]
    
    # Parse query parameters if any
    query_params = {}
    if parsed_uri.query:
        query_params = parse_qs(parsed_uri.query)
        # Convert lists to single values for simplicity
        for key, value in query_params.items():
            if isinstance(value, list) and len(value) == 1:
                query_params[key] = value[0]
    
    # Split the path into components
    path_components = path.split('/')
    
    if not path_components:
        raise ValueError("Invalid URI: empty path")
    
    resource_type = path_components[0]
    
    contents = []
    
    # Handle different resource types
    if resource_type == "entity":
        # Handle entity resources
        if len(path_components) < 2:
            raise ValueError("Entity ID is required")
        
        entity_id_or_action = path_components[1]
        
        if entity_id_or_action == "search":
            # Handle entity search
            query = query_params.get("query", "")
            entity_type = query_params.get("type")
            
            if not query:
                raise ValueError("Search query is required")
            
            entity_types = None
            if entity_type:
                entity_types = [entity_type]
            
            search_results = QUERY_ENGINE.search_entities(query, entity_types)
            
            contents.append({
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps({
                    "query": query,
                    "entity_type": entity_type,
                    "results": search_results
                }, indent=2)
            })
        else:
            # Handle specific entity by ID
            entity_id = entity_id_or_action
            entity_info = QUERY_ENGINE.query_entity(entity_id)
            
            contents.append({
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(entity_info, indent=2)
            })
    
    elif resource_type == "relationship":
        # Handle relationship resources
        if len(path_components) < 2:
            raise ValueError("Relationship ID is required")
        
        relationship_id = path_components[1]
        relationship_info = QUERY_ENGINE.get_relationship(relationship_id)
        
        if not relationship_info:
            raise ValueError(f"Relationship '{relationship_id}' not found")
        
        contents.append({
            "uri": uri,
            "mimeType": "application/json",
            "text": json.dumps(relationship_info, indent=2)
        })
    
    elif resource_type == "section":
        # Handle section resources
        if len(path_components) < 2:
            raise ValueError("Section number is required")
        
        section_num = int(path_components[1])
        
        if section_num not in QUERY_ENGINE.structured_ontology:
            raise ValueError(f"Section {section_num} not found")
        
        section_data = QUERY_ENGINE.structured_ontology[section_num]
        
        if len(path_components) > 2:
            # Handle subsection
            subsection_name = path_components[2]
            subsection_content = QUERY_ENGINE.get_subsection_content(section_num, subsection_name)
            
            contents.append({
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps({
                    "section_num": section_num,
                    "section_title": section_data.get("title", ""),
                    "subsection": subsection_name,
                    "content": subsection_content
                }, indent=2)
            })
        else:
            # Return the entire section
            contents.append({
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(section_data, indent=2)
            })
    
    elif resource_type == "entity_type":
        # Handle entity type resources
        if len(path_components) < 2:
            raise ValueError("Entity type name is required")
        
        entity_type = path_components[1]
        entity_types = QUERY_ENGINE.get_entity_types()
        
        if entity_type not in entity_types:
            raise ValueError(f"Entity type '{entity_type}' not found")
        
        # Get entities of this type
        entities = []
        for node, attrs in QUERY_ENGINE.graph.nodes(data=True):
            if attrs.get("type") == entity_type:
                entities.append({
                    "id": node,
                    "label": attrs.get("label", node)
                })
        
        contents.append({
            "uri": uri,
            "mimeType": "application/json",
            "text": json.dumps({
                "entity_type": entity_type,
                "count": entity_types[entity_type],
                "entities": entities
            }, indent=2)
        })
    
    elif resource_type == "relationship_type":
        # Handle relationship type resources
        if len(path_components) < 2:
            raise ValueError("Relationship type name is required")
        
        rel_type = path_components[1]
        rel_types = QUERY_ENGINE.get_relationship_types()
        
        if rel_type not in rel_types:
            raise ValueError(f"Relationship type '{rel_type}' not found")
        
        # Get relationships of this type
        relationships = []
        for source, target, data in QUERY_ENGINE.graph.edges(data=True):
            if data.get("label") == rel_type:
                relationships.append({
                    "id": data.get("id", f"{source}_{target}"),
                    "source": source,
                    "source_label": QUERY_ENGINE.graph.nodes[source].get("label", source),
                    "target": target,
                    "target_label": QUERY_ENGINE.graph.nodes[target].get("label", target)
                })
        
        contents.append({
            "uri": uri,
            "mimeType": "application/json",
            "text": json.dumps({
                "relationship_type": rel_type,
                "count": rel_types[rel_type],
                "relationships": relationships
            }, indent=2)
        })
    
    elif resource_type == "paths":
        # Handle paths resources
        source_id = query_params.get("source")
        target_id = query_params.get("target")
        max_length = int(query_params.get("max_length", 3))
        
        if not source_id or not target_id:
            raise ValueError("Source and target parameters are required")
        
        paths = QUERY_ENGINE.find_paths(source_id, target_id, max_length)
        
        contents.append({
            "uri": uri,
            "mimeType": "application/json",
            "text": json.dumps({
                "source": source_id,
                "target": target_id,
                "max_length": max_length,
                "paths": paths
            }, indent=2)
        })
    
    elif resource_type == "connections":
        # Handle connections resources
        if len(path_components) < 2:
            raise ValueError("Entity ID is required")
        
        entity_id = path_components[1]
        max_distance = int(query_params.get("max_distance", 2))
        
        connections = QUERY_ENGINE.find_connections(entity_id, max_distance)
        
        contents.append({
            "uri": uri,
            "mimeType": "application/json",
            "text": json.dumps({
                "entity_id": entity_id,
                "max_distance": max_distance,
                "connections": connections
            }, indent=2)
        })
    
    elif resource_type == "graph":
        # Handle graph resources
        if len(path_components) < 2:
            raise ValueError("Graph resource type is required")
        
        graph_resource = path_components[1]
        
        if graph_resource == "summary":
            # Generate graph summary
            summary = QUERY_ENGINE.generate_ontology_summary()
            
            contents.append({
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(summary, indent=2)
            })
        else:
            raise ValueError(f"Unknown graph resource: {graph_resource}")
    
    else:
        raise ValueError(f"Unknown resource type: {resource_type}")
    
    return {
        "contents": contents
    }

def resource_subscription_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle a resources/subscribe request.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        Empty result if successful
    """
    uri = params.get("uri")
    if not uri:
        raise ValueError("URI is required")
    
    # Note: This is a simplified implementation that doesn't actually create
    # a real subscription, since the current version doesn't support real-time updates.
    # In a real implementation, we would store the subscription and send
    # notifications when resources change.
    
    logger.info(f"Subscription requested for URI: {uri} (transport: {transport_id})")
    
    return {}

def resource_unsubscription_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle a resources/unsubscribe request.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        Empty result if successful
    """
    uri = params.get("uri")
    if not uri:
        raise ValueError("URI is required")
    
    # Note: This is a simplified implementation that doesn't actually manage
    # real subscriptions, since the current version doesn't support real-time updates.
    
    logger.info(f"Unsubscription requested for URI: {uri} (transport: {transport_id})")
    
    return {}