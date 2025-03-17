# CYBERON MCP Server

CYBERON now includes support for the Model Context Protocol (MCP), providing a structured way for LLMs and other clients to interact with the cybernetics ontology.

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

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "cyberon/search",
  "params": {
    "query": "cybernetics",
    "limit": 5
  }
}
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
      ...
    ],
    "query": "cybernetics",
    "total": 5
  }
}
```

### Using Resources

Listing available resources:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "resources/list",
  "params": {}
}
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
      ...
    ]
  }
}
```

Reading a resource:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "resources/read",
  "params": {
    "uri": "cyberon:///entity/cybernetics"
  }
}
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