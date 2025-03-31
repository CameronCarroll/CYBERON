# CYBERON MCP Server

CYBERON now includes support for the Model Context Protocol (MCP), providing a structured way for LLMs and other clients to interact with the cybernetics ontology.

_Does MCP stand for Mind Control Protocol? I am... pretty sure yes._

## Overview

The Model Context Protocol integration allows:

- Searching for entities in the ontology
- Retrieving detailed information about entities
- Finding paths between entities
- Discovering connected entities
- Accessing ontology data as structured resources
- Using resource templates for dynamic access

## Running the MCP Server

### Standalone Mode

Run the MCP server as a standalone process:

```bash
python mcp_server.py --data-file /path/to/cybernetics_ontology.json
```

Options:
- `--data-file`: Path to the ontology data file (default: data/cybernetics_ontology.json)
- `--debug`: Enable debug logging
- `--transport`: Transport to use (currently only 'stdio' is supported)

### Integrated with Web API

When running the Flask application, the MCP server is automatically started:

```bash
python run.py
```

You can disable the MCP server by setting the environment variable:

```bash
export MCP_ENABLED=false
python run.py
```

## Available Methods

The MCP server supports the following methods:

### Core Protocol

- `initialize`: Initialize the MCP connection
- `server/capabilities`: Get server capabilities

### CYBERON-specific Tools

- `cyberon/search`: Search for entities
  - Parameters:
    - `query` (string): The search term
    - `entity_types` (array, optional): Filter by entity types
    - `limit` (number, optional): Maximum number of results (default: 10)

- `cyberon/entity`: Get entity details
  - Parameters:
    - `entity_id` (string): The ID of the entity to retrieve

- `cyberon/paths`: Find paths between entities
  - Parameters:
    - `source_id` (string): Source entity ID
    - `target_id` (string): Target entity ID
    - `max_length` (number, optional): Maximum path length (default: 3)

- `cyberon/connections`: Find connected entities
  - Parameters:
    - `entity_id` (string): Entity ID to find connections for
    - `max_distance` (number, optional): Maximum distance to search (default: 2)

- `cyberon/entity_types`: Get all entity types in the ontology
  - Parameters: none

- `cyberon/relationship_types`: Get all relationship types in the ontology
  - Parameters: none

### Resource Methods

- `resources/list`: List available resources
  - Parameters:
    - `cursor` (string, optional): Pagination cursor

- `resources/templates/list`: List resource templates
  - Parameters:
    - `cursor` (string, optional): Pagination cursor

- `resources/read`: Read a resource
  - Parameters:
    - `uri` (string): The URI of the resource to read

- `resources/subscribe`: Subscribe to resource updates
  - Parameters:
    - `uri` (string): The URI of the resource to subscribe to

- `resources/unsubscribe`: Unsubscribe from resource updates
  - Parameters:
    - `uri` (string): The URI of the resource to unsubscribe from

### Tool Methods

- `tools/list`: List available tools
  - Parameters: none

- `tools/schema`: Get schema for a specific tool
  - Parameters:
    - `name` (string): The name of the tool

- `tools/execute`: Execute a tool
  - Parameters:
    - `name` (string): The name of the tool to execute
    - `params` (object): Parameters for the tool

### Resource URI Scheme

Resources are accessed using URIs with the following structure:

```
cyberon:///{resource_type}/{resource_id}[?{query_params}]
```

Available resource types:
- `entity`: Access entity details (e.g., `cyberon:///entity/node1`)
- `entity/search`: Search for entities (e.g., `cyberon:///entity/search?query=system`)
- `relationship`: Access relationship details (e.g., `cyberon:///relationship/edge1`)
- `section`: Access section content (e.g., `cyberon:///section/1`)
- `entity_type`: Access entities of a specific type (e.g., `cyberon:///entity_type/concept`)
- `relationship_type`: Access relationships of a specific type (e.g., `cyberon:///relationship_type/related_to`)
- `paths`: Find paths between entities (e.g., `cyberon:///paths?source=node1&target=node2`)
- `connections`: Find connected entities (e.g., `cyberon:///connections/node1?max_distance=2`)
- `graph/summary`: Get a summary of the ontology graph

## Example Usage

### Using Query Tools

Here's an example of using the search tool:

```
{"jsonrpc":"2.0","id":1,"method":"cyberon/search","params":{"query":"cybernetics","limit":5}}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "entities": [
      {
        "id": "cybernetics",
        "label": "Cybernetics",
        "type": "concept",
        "match_score": 1.0
      },
      // ... (rest of the entities omitted for brevity)
    ],
    "query": "cybernetics",
    "total": 5
  }
}
```

### Using Resources

Listing available resources:

```
{"jsonrpc":"2.0","id":2,"method":"resources/list","params":{}}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "resources": [
      {
        "name": "Entity Type: concept",
        "uri": "cyberon:///entity_type/concept",
        "description": "Information about the 'concept' entity type (15 entities)",
        "mimeType": "application/json"
      },
      {
        "name": "Graph Summary",
        "uri": "cyberon:///graph/summary",
        "description": "Summary information about the ontology graph",
        "mimeType": "application/json"
      },
      // ... (rest of the resources omitted for brevity)
    ]
  }
}
```

Reading a resource:

```
{"jsonrpc":"2.0","id":3,"method":"resources/read","params":{"uri":"cyberon:///entity/cybernetics"}}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "contents": [
      {
        "uri": "cyberon:///entity/cybernetics",
        "mimeType": "application/json",
        "text": "{\n  \"id\": \"cybernetics\",\n  \"attributes\": {\n    \"label\": \"Cybernetics\",\n    \"type\": \"concept\"\n  },\n  \"incoming\": [...],\n  \"outgoing\": [...]\n}"
      }
    ]
  }
}
```

## Integration with LLMs

The MCP server is designed to work with Claude and other LLMs that support the Model Context Protocol. It provides structured access to the cybernetics ontology, allowing LLMs to:

1. Explore the ontology
2. Answer questions about entities and relationships
3. Find connections between concepts
4. Navigate the knowledge graph

### Client Integration

An example MCP client is provided in `app/mcp/client.py` that demonstrates:

1. Proper initialization and capability negotiation
2. Correct JSON-RPC message formatting
3. Structured error handling
4. Examples for all supported MCP methods
5. Feature detection and conditional execution

LLM clients can follow this reference implementation to integrate with the MCP server, especially for:

```python
# Example of initializing a connection
client = MCPClient(transport)
client.initialize()

# Example of executing a tool
results = client.execute_tool("cyberon.tools.search", {"query": "cybernetics"})

# Example of getting a prompt
prompt = client.get_prompt("cyberon.prompts.entity_analysis", {"entity_id": "cybernetics"})
```

The client implements all MCP methods and handles feature detection, ensuring compatibility with different server configurations.

## Development and Testing

To run the MCP tests:

```bash
pytest app/tests/mcp/
```

## Implementation Details

See the following files for implementation details:

- `WP1_IMPLEMENTATION_REPORT.md`: Core MCP server implementation
- `WP2_IMPLEMENTATION_REPORT.md`: Query engine integration
- `WP3_IMPLEMENTATION_REPORT.md`: Resource implementation
- `WP4_IMPLEMENTATION_REPORT.md`: Basic tools implementation
- `WP5_IMPLEMENTATION_REPORT.md`: Advanced tools implementation
- `WP6_IMPLEMENTATION_REPORT.md`: Prompts implementation
- `WP7_IMPLEMENTATION_REPORT.md`: Integration testing and examples

## Using Tools

Listing available tools:

```
{"jsonrpc":"2.0","id":4,"method":"tools/list","params":{}}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "tools": [
      {
        "name": "cyberon.tools.search",
        "description": "Search for entities in the cybernetics ontology",
        "schema": {
          "type": "object",
          "properties": {
            "query": {"type": "string", "description": "The search query"},
            "entity_types": {"type": "array", "items": {"type": "string"}, "description": "Optional filter by entity types"},
            "limit": {"type": "integer", "description": "Maximum number of results to return", "default": 10}
          },
          "required": ["query"]
        }
      },
      // ... (other tools omitted for brevity)
    ]
  }
}
```

Getting a tool schema:

```
{"jsonrpc":"2.0","id":5,"method":"tools/schema","params":{"name":"cyberon.tools.analyze_entity"}}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "name": "cyberon.tools.analyze_entity",
    "schema": {
      "type": "object",
      "properties": {
        "entity_id": {"type": "string", "description": "The ID of the entity to analyze"}
      },
      "required": ["entity_id"]
    }
  }
}
```

Executing a tool:

```
{"jsonrpc":"2.0","id":6,"method":"tools/execute","params":{"name":"cyberon.tools.analyze_entity","params":{"entity_id":"cybernetics"}}}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": {
    "name": "cyberon.tools.analyze_entity",
    "timestamp": "2023-07-14T15:21:36.123456",
    "result": {
      "entity": {
        "id": "cybernetics",
        "label": "Cybernetics",
        "type": "concept"
      },
      "stats": {
        "incoming_relationships": 15,
        "outgoing_relationships": 8,
        "total_relationships": 23,
        "relationship_types": {
          "related_to": 12,
          "part_of": 5,
          "influenced_by": 6
        }
      },
      "top_connected": [
        {"id": "information_theory", "count": 3},
        {"id": "systems_theory", "count": 2},
        {"id": "control_theory", "count": 2},
        {"id": "second_order_cybernetics", "count": 1},
        {"id": "feedback", "count": 1}
      ]
    }
  }
}
```

## Advanced Tools

The MCP server provides advanced ontology analysis tools that extend the basic tools with more sophisticated capabilities:

### Concept Hierarchy Analysis

```
{"jsonrpc":"2.0","id":7,"method":"tools/execute","params":{"name":"cyberon.tools.concept_hierarchy","params":{"include_full_hierarchy":true,"root_concept_id":"cybernetics"}}}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "result": {
    "name": "cyberon.tools.concept_hierarchy",
    "timestamp": "2023-07-14T15:24:12.456789",
    "result": {
      "root_concept": {
        "id": "cybernetics",
        "label": "Cybernetics",
        "type": "concept",
        "max_depth": 4
      },
      "hierarchy": {
        "0": [{"id": "cybernetics", "label": "Cybernetics", "type": "concept"}],
        "1": [
          {"id": "first_order_cybernetics", "label": "First-Order Cybernetics", "type": "concept"},
          {"id": "second_order_cybernetics", "label": "Second-Order Cybernetics", "type": "concept"}
        ],
        "2": [
          {"id": "control_systems", "label": "Control Systems", "type": "concept"},
          {"id": "feedback_loops", "label": "Feedback Loops", "type": "concept"}
        ]
        // ... (hierarchy truncated for brevity)
      },
      "max_depth": 4
    }
  }
}
```

### Related Concepts Discovery

```
{"jsonrpc":"2.0","id":8,"method":"tools/execute","params":{"name":"cyberon.tools.related_concepts","params":{"concept_id":"cybernetics","relationship_types":["influenced_by","part_of"],"include_inverse":true}}}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "result": {
    "name": "cyberon.tools.related_concepts",
    "timestamp": "2023-07-14T15:26:45.123456",
    "result": {
      "concept": {
        "id": "cybernetics",
        "label": "Cybernetics",
        "type": "concept"
      },
      "related_concepts": {
        "influenced_by": [
          {"id": "systems_theory", "label": "Systems Theory", "type": "concept", "direction": "outgoing"}
        ],
        "part_of": [
          {"id": "control_theory", "label": "Control Theory", "type": "concept", "direction": "outgoing"}
        ],
        "inverse_part_of": [
          {"id": "first_order_cybernetics", "label": "First-Order Cybernetics", "type": "concept", "direction": "incoming"},
          {"id": "second_order_cybernetics", "label": "Second-Order Cybernetics", "type": "concept", "direction": "incoming"}
        ]
      },
      "relationship_count": 4
    }
  }
}
```

### Enhanced Central Entities Search

```
{"jsonrpc":"2.0","id":9,"method":"tools/execute","params":{"name":"cyberon.tools.central_entities","params":{"limit":5,"entity_type":"concept","centrality_metric":"degree","min_connections":3}}}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "result": {
    "name": "cyberon.tools.central_entities",
    "timestamp": "2023-07-14T15:28:30.789012",
    "result": {
      "entities": [
        {"id": "cybernetics", "label": "Cybernetics", "type": "concept", "centrality": 0.95, "connections": 23},
        {"id": "systems_theory", "label": "Systems Theory", "type": "concept", "centrality": 0.82, "connections": 18},
        {"id": "information_theory", "label": "Information Theory", "type": "concept", "centrality": 0.78, "connections": 15},
        {"id": "complexity", "label": "Complexity", "type": "concept", "centrality": 0.65, "connections": 12},
        {"id": "feedback", "label": "Feedback", "type": "concept", "centrality": 0.61, "connections": 10}
      ],
      "entities_by_type": {
        "concept": [
          // ... (same entities as above omitted for brevity)
        ]
      },
      "centrality_metric": "degree",
      "total": 5
    }
  }
}
```

### Concept Evolution Tracing

```
{"jsonrpc":"2.0","id":10,"method":"tools/execute","params":{"name":"cyberon.tools.concept_evolution","params":{"concept_id":"cybernetics"}}}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "result": {
    "name": "cyberon.tools.concept_evolution",
    "timestamp": "2023-07-14T15:30:15.456789",
    "result": {
      "evolution_chains": [
        [
          {"id": "control_theory", "label": "Control Theory", "type": "concept"},
          {"id": "cybernetics", "label": "Cybernetics", "type": "concept"},
          {"id": "second_order_cybernetics", "label": "Second-Order Cybernetics", "type": "concept"},
          {"id": "organizational_cybernetics", "label": "Organizational Cybernetics", "type": "concept"}
        ]
      ],
      "chain_count": 1,
      "concept_id": "cybernetics"
    }
  }
}
```

## Using Prompts

The MCP server provides prompt templates for interacting with the cybernetics ontology using natural language. These prompts can be easily used with LLMs that support the MCP protocol.

### Listing Available Prompts

```
{"jsonrpc":"2.0","id":11,"method":"prompts/list","params":{}}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 11,
  "result": {
    "prompts": [
      {
        "name": "cyberon.prompts.entity_analysis",
        "description": "Analyze a specific entity in the cybernetics ontology",
        "parameter_schema": { /* ... schema details ... */ },
        "usage_examples": [ /* ... examples ... */ ]
      },
      {
        "name": "cyberon.prompts.concept_comparison",
        "description": "Compare two concepts in the cybernetics ontology",
        "parameter_schema": { /* ... schema details ... */ },
        "usage_examples": [ /* ... examples ... */ ]
      },
      {
        "name": "cyberon.prompts.ontology_exploration",
        "description": "Explore a topic within the cybernetics ontology",
        "parameter_schema": { /* ... schema details ... */ },
        "usage_examples": [ /* ... examples ... */ ]
      }
      // ... (other prompts omitted for brevity)
    ]
  }
}
```

### Generating a Prompt

```
{"jsonrpc":"2.0","id":12,"method":"prompts/get","params":{"name":"cyberon.prompts.entity_analysis","params":{"entity_id":"cybernetics"}}}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 12,
  "result": {
    "name": "cyberon.prompts.entity_analysis",
    "timestamp": "2023-07-14T15:35:22.987654",
    "prompt": "Please analyze the concept 'Cybernetics' from the cybernetics ontology. Based on the information below, provide a comprehensive explanation of what Cybernetics is, its significance, and how it relates to other concepts in cybernetics.\n\nWhen analyzing, please consider:\n1. The key characteristics of Cybernetics\n2. Its relationship to other concepts in cybernetics\n3. Its historical development and importance\n4. Real-world applications or examples\n\nPlease format your response with clear headings and concise paragraphs.",
    "context": {
      "entity": { /* ... entity details ... */ },
      "entity_summary": "Cybernetics (concept)",
      "relationships": [ /* ... relationship details ... */ ]
    }
  }
}
```

### Advanced Prompts

#### Concept Comparison

```
{"jsonrpc":"2.0","id":13,"method":"prompts/get","params":{"name":"cyberon.prompts.concept_comparison","params":{"concept1_id":"first_order_cybernetics","concept2_id":"second_order_cybernetics"}}}
```

#### Hierarchy Analysis

```
{"jsonrpc":"2.0","id":14,"method":"prompts/get","params":{"name":"cyberon.prompts.hierarchy_analysis","params":{"root_concept_id":"cybernetics"}}}
```

#### Central Concepts Analysis

```
{"jsonrpc":"2.0","id":15,"method":"prompts/get","params":{"name":"cyberon.prompts.central_concepts","params":{"limit":5,"entity_type":"concept"}}}
```