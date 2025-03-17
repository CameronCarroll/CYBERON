# Work Package 6: Prompts Implementation

## Overview

This document provides a detailed report on the implementation of Work Package 6 (WP6) for the CYBERON project. WP6 extends the Model Context Protocol (MCP) server capabilities by adding prompt templates for ontology exploration, building on top of the advanced analysis tools implemented in WP5.

## Implementation Details

### Core Components

1. **Prompt Registration and Management System**:
   - Created a centralized prompt registry
   - Implemented parameter schema validation using JSON Schema
   - Added support for custom handlers and template-based prompts
   - Implemented usage examples for each prompt

2. **Prompt Listing Endpoint**:
   - Implemented the `prompts/list` endpoint to discover available prompts
   - Each prompt listing includes name, description, parameter schema, and usage examples

3. **Prompt Generation Endpoint**:
   - Implemented the `prompts/get` endpoint to generate prompts with parameters
   - Added support for both simple template-based prompts and custom handler-based prompts
   - Implemented rich context generation for better prompt understanding

4. **Specialized Prompt Templates**:
   - Created 5 specialized prompt templates for different ontology exploration tasks:
     - Entity Analysis (`cyberon.prompts.entity_analysis`)
     - Concept Comparison (`cyberon.prompts.concept_comparison`)
     - Ontology Exploration (`cyberon.prompts.ontology_exploration`)
     - Hierarchy Analysis (`cyberon.prompts.hierarchy_analysis`)
     - Central Concepts Analysis (`cyberon.prompts.central_concepts`)

5. **Custom Prompt Handlers**:
   - Each specialized prompt has a custom handler that generates:
     - A natural language prompt template
     - Rich context information about the entities and relationships
     - Structured data that can be used by LLMs for better reasoning

### File Changes

The following files were created or modified during the implementation:

1. `/app/mcp/handlers/prompts.py`: 
   - Core implementation of prompt handlers
   - Prompt registration system
   - Template processing functions
   - Custom handlers for specialized prompts

2. `/app/mcp/handlers/__init__.py`:
   - Added imports for prompt handlers
   - Updated exports list to include prompt functions

3. `/app/mcp/server.py`:
   - Updated server capabilities to enable prompts feature
   - Added prompt handler registration
   - Added query engine setup for prompt handlers
   - Set up default prompt registration

4. `/app/tests/mcp/test_prompt_integration.py`:
   - Comprehensive tests for all prompt functionality
   - Tests for each specialized prompt handler
   - Tests for edge cases and error conditions

## Prompt Templates

### 1. Entity Analysis Prompt

This prompt template helps generate a comprehensive analysis of a specific entity in the cybernetics ontology. It provides:

- A natural language prompt asking for an analysis of the entity
- Context information about the entity's attributes
- Relationship information showing connections to other entities

```json
{
  "name": "cyberon.prompts.entity_analysis",
  "description": "Analyze a specific entity in the cybernetics ontology",
  "template": "Please analyze the entity '{entity_id}' from the cybernetics ontology.",
  "parameter_schema": {
    "type": "object",
    "properties": {
      "entity_id": {
        "type": "string",
        "description": "The ID of the entity to analyze"
      }
    },
    "required": ["entity_id"]
  }
}
```

### 2. Concept Comparison Prompt

This prompt template facilitates comparison between two concepts in the cybernetics ontology. It provides:

- A natural language prompt asking for a comparison
- Context information about both concepts
- Relationship paths between the concepts
- Analysis of common and different properties

```json
{
  "name": "cyberon.prompts.concept_comparison",
  "description": "Compare two concepts in the cybernetics ontology",
  "template": "Please compare the concepts '{concept1_id}' and '{concept2_id}' from the cybernetics ontology.",
  "parameter_schema": {
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
  }
}
```

### 3. Ontology Exploration Prompt

This prompt template supports exploration of topics within the cybernetics ontology. It provides:

- A natural language prompt focused on a specific topic
- Search results related to the topic
- Ontology summary statistics
- Related sections from the structured ontology

```json
{
  "name": "cyberon.prompts.ontology_exploration",
  "description": "Explore a topic within the cybernetics ontology",
  "template": "Please explore the topic '{topic}' within the cybernetics ontology.",
  "parameter_schema": {
    "type": "object",
    "properties": {
      "topic": {
        "type": "string",
        "description": "The topic to explore"
      }
    },
    "required": ["topic"]
  }
}
```

### 4. Hierarchy Analysis Prompt

This prompt template facilitates analysis of concept hierarchies in the ontology. It provides:

- A natural language prompt for hierarchy analysis
- Information about root concepts and their hierarchies
- Depth and breadth statistics of the hierarchical structure
- Option to focus on a specific root concept

```json
{
  "name": "cyberon.prompts.hierarchy_analysis",
  "description": "Analyze concept hierarchies in the cybernetics ontology",
  "template": "Please analyze the concept hierarchies in the cybernetics ontology.",
  "parameter_schema": {
    "type": "object",
    "properties": {
      "root_concept_id": {
        "type": "string",
        "description": "Optional specific root concept to analyze"
      }
    }
  }
}
```

### 5. Central Concepts Analysis Prompt

This prompt template supports analysis of the most central concepts in the ontology. It provides:

- A natural language prompt for analyzing central concepts
- Centrality metrics for key concepts
- Grouping of central concepts by type
- Option to filter by entity type and limit results

```json
{
  "name": "cyberon.prompts.central_concepts",
  "description": "Analyze the most central concepts in the cybernetics ontology",
  "template": "Please analyze the most central concepts in the cybernetics ontology.",
  "parameter_schema": {
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
  }
}
```

## Testing

All implemented prompt handlers have been thoroughly tested with both unit and integration tests. The testing approach included:

1. **Mock-based Unit Testing**:
   - Each prompt handler was tested with mock query engine responses
   - Tests verify both correct processing and proper error handling
   - Tests ensure correct parameter validation

2. **Template Processing Testing**:
   - Tests verify that template placeholders are properly replaced
   - Tests ensure template processing handles missing parameters gracefully

3. **Prompt Listing Testing**:
   - Tests verify that prompts can be discovered through the list endpoint
   - Tests ensure prompt listings include all required metadata

4. **Prompt Generation Testing**:
   - Tests verify that prompts are generated correctly for all handlers
   - Tests ensure parameter validation works correctly
   - Tests ensure context information is properly included

## Integration with MCP Protocol

The implementation integrates seamlessly with the MCP protocol:

1. **Server Capabilities**:
   - Updated the server capabilities to indicate support for prompts
   - Added prompts to the supported features list

2. **Endpoint Registration**:
   - Registered new handlers for `prompts/list` and `prompts/get`
   - Set up proper parameter validation

3. **Query Engine Integration**:
   - Set up query engine access for prompt handlers
   - Ensured all handlers can efficiently access ontology data

4. **Default Prompt Registration**:
   - Automatically registered all standard prompts at server startup
   - Set up a flexible system for extending with new prompts

## Usage Examples

### Listing Available Prompts

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "prompts/list",
  "params": {}
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "prompts": [
      {
        "name": "cyberon.prompts.entity_analysis",
        "description": "Analyze a specific entity in the cybernetics ontology",
        "parameter_schema": {
          "type": "object",
          "properties": {
            "entity_id": {
              "type": "string",
              "description": "The ID of the entity to analyze"
            }
          },
          "required": ["entity_id"]
        },
        "usage_examples": [
          {
            "description": "Analyze the 'cybernetics' concept",
            "params": {
              "entity_id": "cybernetics"
            }
          }
        ]
      },
      ...
    ]
  }
}
```

### Getting a Specific Prompt

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "prompts/get",
  "params": {
    "name": "cyberon.prompts.entity_analysis",
    "params": {
      "entity_id": "cybernetics"
    }
  }
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "name": "cyberon.prompts.entity_analysis",
    "timestamp": "2023-07-14T15:21:36.123456",
    "prompt": "Please analyze the concept 'Cybernetics' from the cybernetics ontology. Based on the information below, provide a comprehensive explanation of what Cybernetics is, its significance, and how it relates to other concepts in cybernetics...",
    "context": {
      "entity": {
        "id": "cybernetics",
        "attributes": {
          "label": "Cybernetics",
          "type": "concept"
        },
        "incoming": [...],
        "outgoing": [...]
      },
      "entity_summary": "Cybernetics (concept)",
      "relationships": [...]
    }
  }
}
```

## Conclusion

The implementation of Work Package 6 has successfully enhanced the CYBERON MCP server with prompt templates for ontology exploration. These prompts provide sophisticated ways for LLMs and other clients to interact with the cybernetics ontology using natural language templates and rich context information.

This implementation builds on the foundation established in previous work packages, particularly leveraging the advanced tools from Work Package 5. The prompt system provides an intuitive and powerful interface for interacting with the ontology that is optimized for Large Language Models, making it easier to generate comprehensive analyses and explanations using the ontology data.

The next logical step would be Work Package 7: Integration Testing and Examples, which would focus on comprehensive integration testing of all the components together, creating end-to-end examples, and preparing the system for deployment.