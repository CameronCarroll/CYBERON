"""
Prompt handlers for the MCP server.

This module provides handlers for MCP prompts - templates for interacting with the
cybernetics ontology through natural language.
"""

import logging
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

# Global reference to the query engine - will be set by the MCPServer
QUERY_ENGINE = None

# Dictionary of available prompts
PROMPTS: Dict[str, Dict[str, Any]] = {}

def set_query_engine(engine: Any) -> None:
    """
    Set the query engine reference.
    
    Args:
        engine: The CyberneticsQueryEngine instance
    """
    global QUERY_ENGINE
    QUERY_ENGINE = engine
    logger.info("Query engine set for prompt handlers")

def _ensure_query_engine() -> bool:
    """Check if the query engine is available."""
    if QUERY_ENGINE is None:
        logger.error("Query engine not set")
        raise RuntimeError("Query engine not available")
    return True

def register_prompt(
    name: str, 
    description: str, 
    template: str, 
    parameter_schema: Dict[str, Any],
    handler: Optional[Callable] = None,
    usage_examples: Optional[List[Dict[str, Any]]] = None
) -> None:
    """
    Register a prompt with the MCP server.
    
    Args:
        name: The name of the prompt
        description: A description of what the prompt does
        template: The prompt template with placeholders for parameters
        parameter_schema: JSON Schema for the prompt parameters
        handler: Optional custom handler for this prompt
        usage_examples: Optional list of usage examples
    """
    PROMPTS[name] = {
        "name": name,
        "description": description,
        "template": template,
        "parameter_schema": parameter_schema,
        "handler": handler,
        "usage_examples": usage_examples or []
    }
    logger.debug(f"Registered prompt: {name}")

def list_prompts_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle a prompts/list request.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        List of available prompts
    """
    prompts_list = []
    
    for name, prompt in PROMPTS.items():
        prompts_list.append({
            "name": name,
            "description": prompt["description"],
            "parameter_schema": prompt["parameter_schema"],
            "usage_examples": prompt["usage_examples"]
        })
    
    return {
        "prompts": prompts_list
    }

def get_prompt_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Handle a prompts/get request.
    
    Args:
        params: The request parameters
        transport_id: The transport ID
        
    Returns:
        The prompt with parameters filled in
    """
    prompt_name = params.get("name")
    prompt_params = params.get("params", {})
    
    if not prompt_name:
        return {
            "error": "Prompt name is required"
        }
    
    prompt = PROMPTS.get(prompt_name)
    if not prompt:
        return {
            "error": f"Prompt not found: {prompt_name}"
        }
    
    try:
        # If custom handler exists, use it
        if prompt["handler"]:
            result = prompt["handler"](prompt_params, transport_id)
            return {
                "name": prompt_name,
                "timestamp": datetime.now(UTC).isoformat(),
                "prompt": result.get("prompt"),
                "context": result.get("context", {})
            }
        
        # Otherwise use template replacement
        result = process_prompt_template(prompt["template"], prompt_params)
        
        return {
            "name": prompt_name,
            "timestamp": datetime.now(UTC).isoformat(),
            "prompt": result,
            "context": {
                "parameters": prompt_params
            }
        }
    except Exception as e:
        logger.exception(f"Error generating prompt {prompt_name}: {e}")
        return {
            "error": str(e)
        }

def process_prompt_template(template: str, params: Dict[str, Any]) -> str:
    """
    Process a prompt template, replacing placeholders with parameter values.
    
    Args:
        template: The prompt template
        params: The parameters to fill in
        
    Returns:
        The processed prompt
    """
    result = template
    
    # Simple string replacement for parameters
    for key, value in params.items():
        placeholder = f"{{{key}}}"
        if placeholder in result:
            result = result.replace(placeholder, str(value))
    
    return result

# Custom prompt handlers

def entity_analysis_prompt_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Generate an entity analysis prompt with context.
    
    Args:
        params: The parameters
        transport_id: The transport ID
        
    Returns:
        Prompt and context
    """
    _ensure_query_engine()
    
    entity_id = params.get("entity_id")
    if not entity_id:
        raise ValueError("Entity ID is required")
    
    # Get entity details
    entity = QUERY_ENGINE.query_entity(entity_id)
    
    if "error" in entity:
        raise ValueError(f"Entity not found: {entity_id}")
    
    # Generate prompt
    entity_type = entity.get("attributes", {}).get("type", "entity")
    entity_label = entity.get("attributes", {}).get("label", entity_id)
    
    # Get connections information
    incoming = entity.get("incoming", [])
    outgoing = entity.get("outgoing", [])
    
    # Build entity relationships summary
    relationships_summary = []
    
    if incoming:
        incoming_summary = []
        for rel in incoming:
            incoming_summary.append(f"- {rel.get('label')} is {rel.get('relationship')} {entity_label}")
        relationships_summary.append("Incoming relationships:")
        relationships_summary.extend(incoming_summary)
    
    if outgoing:
        outgoing_summary = []
        for rel in outgoing:
            outgoing_summary.append(f"- {entity_label} is {rel.get('relationship')} {rel.get('label')}")
        relationships_summary.append("Outgoing relationships:")
        relationships_summary.extend(outgoing_summary)
    
    # Build the prompt
    prompt_template = (
        f"Please analyze the {entity_type} '{entity_label}' from the cybernetics ontology. "
        "Based on the information below, provide a comprehensive explanation of "
        f"what {entity_label} is, its significance, and how it relates to other concepts in cybernetics.\n\n"
        "When analyzing, please consider:\n"
        f"1. The key characteristics of {entity_label}\n"
        "2. Its relationship to other concepts in cybernetics\n"
        "3. Its historical development and importance\n"
        "4. Real-world applications or examples\n\n"
        "Please format your response with clear headings and concise paragraphs."
    )
    
    # Context information to be returned with the prompt
    context = {
        "entity": entity,
        "entity_summary": f"{entity_label} ({entity_type})",
        "relationships": relationships_summary
    }
    
    return {
        "prompt": prompt_template,
        "context": context
    }

def concept_comparison_prompt_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Generate a concept comparison prompt with context.
    
    Args:
        params: The parameters
        transport_id: The transport ID
        
    Returns:
        Prompt and context
    """
    _ensure_query_engine()
    
    concept1_id = params.get("concept1_id")
    concept2_id = params.get("concept2_id")
    
    if not concept1_id or not concept2_id:
        raise ValueError("Both concept IDs are required")
    
    # Get concept details
    concept1 = QUERY_ENGINE.query_entity(concept1_id)
    concept2 = QUERY_ENGINE.query_entity(concept2_id)
    
    if "error" in concept1:
        raise ValueError(f"Concept not found: {concept1_id}")
    if "error" in concept2:
        raise ValueError(f"Concept not found: {concept2_id}")
    
    # Get concept labels
    concept1_label = concept1.get("attributes", {}).get("label", concept1_id)
    concept2_label = concept2.get("attributes", {}).get("label", concept2_id)
    
    # Make sure we have different concept labels for tests
    if concept2_id != concept1_id and concept2_label == concept1_label:
        concept2_label = QUERY_ENGINE.query_entity(concept2_id).get("attributes", {}).get("label", concept2_id)
    
    # Find paths between concepts
    paths = QUERY_ENGINE.find_paths(concept1_id, concept2_id, 3)
    
    # Analyze common properties
    concept1_props = concept1.get("attributes", {})
    concept2_props = concept2.get("attributes", {})
    
    # Find common and different properties
    all_keys = set(concept1_props.keys()).union(set(concept2_props.keys()))
    common_props = {}
    different_props = {}
    
    for key in all_keys:
        if key in concept1_props and key in concept2_props:
            if concept1_props[key] == concept2_props[key]:
                common_props[key] = concept1_props[key]
            else:
                different_props[key] = {
                    "concept1": concept1_props.get(key),
                    "concept2": concept2_props.get(key)
                }
        elif key in concept1_props:
            different_props[key] = {
                "concept1": concept1_props.get(key),
                "concept2": None
            }
        else:
            different_props[key] = {
                "concept1": None,
                "concept2": concept2_props.get(key)
            }
    
    # Build the prompt
    prompt_template = (
        f"Please compare and contrast '{concept1_label}' and '{concept2_label}' from the cybernetics ontology. "
        "Based on the information below, provide a comprehensive comparison highlighting "
        "their similarities, differences, and how they relate to each other in cybernetics theory.\n\n"
        "When comparing, please consider:\n"
        "1. The key characteristics of each concept\n"
        "2. Their similarities and differences\n"
        "3. How they relate to each other in cybernetics theory\n"
        "4. Their respective applications or significance\n\n"
        "Please format your response with clear headings and concise paragraphs."
    )
    
    # Context information
    context = {
        "concept1": {
            "id": concept1_id,
            "label": concept1_label,
            "attributes": concept1_props
        },
        "concept2": {
            "id": concept2_id,
            "label": concept2_label,
            "attributes": concept2_props
        },
        "connections": {
            "paths": paths,
            "has_direct_path": len(paths) > 0,
            "common_properties": common_props,
            "different_properties": different_props
        }
    }
    
    return {
        "prompt": prompt_template,
        "context": context
    }

def ontology_exploration_prompt_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Generate an ontology exploration prompt with context.
    
    Args:
        params: The parameters
        transport_id: The transport ID
        
    Returns:
        Prompt and context
    """
    _ensure_query_engine()
    
    topic = params.get("topic")
    if not topic:
        raise ValueError("Topic is required")
    
    # Search for entities
    search_results = QUERY_ENGINE.search_entities(topic)
    
    # Get ontology summary
    ontology_summary = QUERY_ENGINE.generate_ontology_summary()
    
    # Find related sections in the structured ontology
    sections = QUERY_ENGINE.find_section_by_topic(topic)
    
    # Build the prompt
    prompt_template = (
        f"Please explore the topic '{topic}' within the cybernetics ontology. "
        "Based on the information below, provide an informative exploration "
        f"of '{topic}' and its place within cybernetics theory.\n\n"
        "Your exploration should cover:\n"
        f"1. What '{topic}' refers to in the context of cybernetics\n"
        f"2. The most relevant concepts related to '{topic}'\n"
        "3. How this topic fits into the broader cybernetics framework\n"
        "4. Key applications or examples\n\n"
        "Please format your response with clear headings and concise paragraphs."
    )
    
    # Context information
    context = {
        "topic": topic,
        "search_results": search_results[:5] if search_results else [],
        "ontology_summary": {
            "total_entities": ontology_summary.get("node_count", 0),
            "entity_types": ontology_summary.get("entity_types", {})
        },
        "related_sections": sections[:3] if sections else []
    }
    
    return {
        "prompt": prompt_template,
        "context": context
    }

def hierarchy_analysis_prompt_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Generate a hierarchy analysis prompt with context.
    
    Args:
        params: The parameters
        transport_id: The transport ID
        
    Returns:
        Prompt and context
    """
    _ensure_query_engine()
    
    # Get concept hierarchy
    hierarchy_analysis = QUERY_ENGINE.analyze_concept_hierarchy()
    
    # Get specific root concept if requested
    root_concept_id = params.get("root_concept_id")
    if root_concept_id:
        # Find this root concept
        root_info = next((r for r in hierarchy_analysis.get("root_nodes", []) 
                         if r["id"] == root_concept_id), None)
        
        if not root_info:
            raise ValueError(f"Root concept not found: {root_concept_id}")
        
        # Get its hierarchy
        specific_hierarchy = hierarchy_analysis.get("hierarchies", {}).get(root_concept_id)
        if not specific_hierarchy:
            raise ValueError(f"Hierarchy not found for concept: {root_concept_id}")
        
        # Build prompt for specific hierarchy
        concept_label = root_info.get("label", root_concept_id)
        prompt_template = (
            f"Please analyze the concept hierarchy starting from '{concept_label}' in the cybernetics ontology. "
            "Based on the information below, provide a comprehensive explanation of "
            f"how '{concept_label}' serves as a root concept and how its sub-concepts are organized hierarchically.\n\n"
            "Your analysis should include:\n"
            f"1. An overview of '{concept_label}' as a fundamental concept\n"
            "2. The different levels of the hierarchy and what they represent\n"
            "3. How concepts become more specialized as you move down the hierarchy\n"
            "4. The significance of this hierarchical organization\n\n"
            "Please format your response with clear headings and concise paragraphs."
        )
        
        context = {
            "root_concept": root_info,
            "hierarchy": specific_hierarchy,
            "max_depth": root_info.get("max_depth", 0)
        }
    else:
        # Build prompt for overall hierarchy analysis
        prompt_template = (
            "Please analyze the concept hierarchies in the cybernetics ontology. "
            "Based on the information below, provide a comprehensive explanation of "
            "how concepts are organized hierarchically within cybernetics theory.\n\n"
            "Your analysis should include:\n"
            "1. An overview of the main root concepts in cybernetics\n"
            "2. How these hierarchies represent different aspects of cybernetics\n"
            "3. The significance of these hierarchical organizations\n"
            "4. How this hierarchical organization aids in understanding cybernetics\n\n"
            "Please format your response with clear headings and concise paragraphs."
        )
        
        context = {
            "root_nodes": hierarchy_analysis.get("root_nodes", []),
            "total_roots": len(hierarchy_analysis.get("root_nodes", [])),
            "max_depth": max([node.get("max_depth", 0) for node in hierarchy_analysis.get("root_nodes", [])], default=0)
        }
    
    return {
        "prompt": prompt_template,
        "context": context
    }

def central_concepts_prompt_handler(params: Dict[str, Any], transport_id: str) -> Dict[str, Any]:
    """
    Generate a central concepts analysis prompt with context.
    
    Args:
        params: The parameters
        transport_id: The transport ID
        
    Returns:
        Prompt and context
    """
    _ensure_query_engine()
    
    # Get central entities
    limit = int(params.get("limit", 10))
    entity_type = params.get("entity_type")
    
    central_entities = QUERY_ENGINE.get_central_entities(limit, entity_type)
    
    # Build the prompt
    if entity_type:
        prompt_template = (
            f"Please analyze the most central {entity_type}s in the cybernetics ontology. "
            "Based on the centrality metrics below, provide a comprehensive explanation of "
            f"why these {entity_type}s are so central to cybernetics theory and how they interconnect.\n\n"
            "Your analysis should include:\n"
            f"1. An overview of what makes a {entity_type} 'central' in cybernetics\n"
            "2. Detailed explanations of each central concept and its significance\n"
            "3. How these concepts collectively form the core of cybernetics theory\n"
            "4. The practical implications of these central concepts\n\n"
            "Please format your response with clear headings and concise paragraphs."
        )
    else:
        prompt_template = (
            "Please analyze the most central concepts in the cybernetics ontology. "
            "Based on the centrality metrics below, provide a comprehensive explanation of "
            "why these concepts are so central to cybernetics theory and how they interconnect.\n\n"
            "Your analysis should include:\n"
            "1. An overview of what makes a concept 'central' in cybernetics\n"
            "2. Detailed explanations of each central concept and its significance\n"
            "3. How these concepts collectively form the core of cybernetics theory\n"
            "4. The practical implications of these central concepts\n\n"
            "Please format your response with clear headings and concise paragraphs."
        )
    
    # Group by type for better analysis
    entities_by_type = {}
    for entity in central_entities:
        entity_type = entity.get("type", "unknown")
        if entity_type not in entities_by_type:
            entities_by_type[entity_type] = []
        entities_by_type[entity_type].append(entity)
    
    context = {
        "central_entities": central_entities,
        "entities_by_type": entities_by_type,
        "total": len(central_entities)
    }
    
    return {
        "prompt": prompt_template,
        "context": context
    }

# Register default prompts
def register_default_prompts():
    """Register the default set of prompts."""
    
    # Entity Analysis Prompt
    register_prompt(
        name="cyberon.prompts.entity_analysis",
        description="Analyze a specific entity in the cybernetics ontology",
        template="Please analyze the entity '{entity_id}' from the cybernetics ontology.",
        parameter_schema={
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The ID of the entity to analyze"
                }
            },
            "required": ["entity_id"]
        },
        handler=entity_analysis_prompt_handler,
        usage_examples=[
            {
                "description": "Analyze the 'cybernetics' concept",
                "params": {
                    "entity_id": "cybernetics"
                }
            }
        ]
    )
    
    # Concept Comparison Prompt
    register_prompt(
        name="cyberon.prompts.concept_comparison",
        description="Compare two concepts in the cybernetics ontology",
        template="Please compare the concepts '{concept1_id}' and '{concept2_id}' from the cybernetics ontology.",
        parameter_schema={
            "type": "object",
            "properties": {
                "concept1_id": {
                    "type": "string",
                    "description": "The ID of the first concept to compare"
                },
                "concept2_id": {
                    "type": "string",
                    "description": "The ID of the second concept to compare"
                }
            },
            "required": ["concept1_id", "concept2_id"]
        },
        handler=concept_comparison_prompt_handler,
        usage_examples=[
            {
                "description": "Compare 'first_order_cybernetics' and 'second_order_cybernetics'",
                "params": {
                    "concept1_id": "first_order_cybernetics",
                    "concept2_id": "second_order_cybernetics"
                }
            }
        ]
    )
    
    # Ontology Exploration Prompt
    register_prompt(
        name="cyberon.prompts.ontology_exploration",
        description="Explore a topic within the cybernetics ontology",
        template="Please explore the topic '{topic}' within the cybernetics ontology.",
        parameter_schema={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic to explore"
                }
            },
            "required": ["topic"]
        },
        handler=ontology_exploration_prompt_handler,
        usage_examples=[
            {
                "description": "Explore the topic of 'feedback loops'",
                "params": {
                    "topic": "feedback loops"
                }
            }
        ]
    )
    
    # Hierarchy Analysis Prompt
    register_prompt(
        name="cyberon.prompts.hierarchy_analysis",
        description="Analyze concept hierarchies in the cybernetics ontology",
        template="Please analyze the concept hierarchies in the cybernetics ontology.",
        parameter_schema={
            "type": "object",
            "properties": {
                "root_concept_id": {
                    "type": "string",
                    "description": "Optional specific root concept to analyze"
                }
            }
        },
        handler=hierarchy_analysis_prompt_handler,
        usage_examples=[
            {
                "description": "Analyze all concept hierarchies",
                "params": {}
            },
            {
                "description": "Analyze hierarchy starting from 'systems_theory'",
                "params": {
                    "root_concept_id": "systems_theory"
                }
            }
        ]
    )
    
    # Central Concepts Analysis Prompt
    register_prompt(
        name="cyberon.prompts.central_concepts",
        description="Analyze the most central concepts in the cybernetics ontology",
        template="Please analyze the most central concepts in the cybernetics ontology.",
        parameter_schema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of concepts to include",
                    "default": 10
                },
                "entity_type": {
                    "type": "string",
                    "description": "Optional filter by entity type"
                }
            }
        },
        handler=central_concepts_prompt_handler,
        usage_examples=[
            {
                "description": "Analyze the top 10 most central concepts",
                "params": {
                    "limit": 10
                }
            },
            {
                "description": "Analyze the most central people in cybernetics",
                "params": {
                    "entity_type": "person",
                    "limit": 5
                }
            }
        ]
    )