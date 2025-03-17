## API Reference

The Cybernetics Digital Garden provides a RESTful API for programmatic access to the knowledge graph. This allows you to integrate the ontology into other applications, build custom visualizations, or automate content management.

### Authentication

Currently, the API does not require authentication.

### Rate Limiting

To prevent abuse and ensure system stability, the API implements rate limiting. The following limits apply:

- Default limits: 200 requests per day, 50 requests per hour, 10 requests per minute
- Create/Delete operations: 5 requests per minute
- List/Query operations: 30 requests per minute
- Graph traversal operations: 20 requests per minute
- Graph statistics: 10 requests per minute

When you exceed the rate limit, you'll receive a 429 (Too Many Requests) response with details about when you can retry:

```json
{
  "success": false,
  "error": "Too many requests. Please slow down.",
  "retry_after": "1 minute",
  "message": "The API is rate limited to prevent abuse. Please reduce your request frequency."
}
```

Note: Requests from localhost (127.0.0.1, ::1) and certain development IPs are exempt from rate limiting.

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 200 per day
X-RateLimit-Remaining: varies
```

For higher-throughput applications that need to exceed these limits, please contact the API administrator.

### Response Format

All API endpoints return responses in JSON format with a consistent structure:

```json
{
  "success": true,
  "data": { ... }
}
```

For error responses:

```json
{
  "success": false,
  "error": "Error message details"
}
```

### Entity Operations

Entities represent nodes in the knowledge graph (concepts, people, domains).

#### List Entities

```
GET /api/entities
```

Query parameters:
- `type` (optional): Filter by entity type (e.g., "concept", "person")
- `q` (optional): Search term for entity labels and descriptions
- `limit` (optional): Maximum number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)
- `sort` (optional): Field to sort by (default: "created_at")
- `order` (optional): Sort order - "asc" or "desc" (default: "desc")

Response:
```json
{
  "success": true,
  "entities": [
    {
      "id": "entity_id",
      "label": "Entity Label",
      "type": "concept",
      "description": "Entity description",
      "created_at": "2023-01-01T12:00:00Z"
    },
    ...
  ],
  "pagination": {
    "total": 100,
    "offset": 0,
    "limit": 50,
    "next_offset": 50
  }
}
```

#### Get Entity

```
GET /api/entities/{entity_id}
```

Response:
```json
{
  "success": true,
  "entity": {
    "id": "entity_id",
    "attributes": {
      "label": "Entity Label",
      "type": "concept",
      "description": "Entity description",
      "external_url": "https://example.com/resource",
      "created_at": "2023-01-01T12:00:00Z",
      ...
    },
    "incoming": [
      {
        "id": "source_entity_id",
        "label": "Source Entity",
        "relationship": "related_to"
      },
      ...
    ],
    "outgoing": [
      {
        "id": "target_entity_id",
        "label": "Target Entity",
        "relationship": "contains"
      },
      ...
    ]
  }
}
```

#### Create Entity

```
POST /api/entities
```

Request body:
```json
{
  "label": "New Entity",
  "type": "concept",
  "description": "Description of the entity",
  "external_url": "https://example.com/resource",
  "attributes": {
    "custom_field1": "value1",
    "custom_field2": "value2"
  }
}
```

Response:
```json
{
  "success": true,
  "entity": {
    "id": "new_entity_id",
    "attributes": { ... },
    "incoming": [],
    "outgoing": []
  }
}
```

#### Update Entity

```
PUT /api/entities/{entity_id}
```

Request body (only include fields to update):
```json
{
  "label": "Updated Label",
  "description": "Updated description",
  "external_url": "https://example.com/updated-resource",
  "attributes": {
    "custom_field1": "new_value"
  }
}
```

Response:
```json
{
  "success": true,
  "entity": {
    "id": "entity_id",
    "attributes": { ... }
  }
}
```

#### Delete Entity

```
DELETE /api/entities/{entity_id}
```

Query parameters:
- `cascade` (optional): Whether to delete relationships (default: false)

Response:
```json
{
  "success": true,
  "message": "Entity deleted successfully",
  "relationships_removed": 3
}
```

### Relationship Operations

Relationships represent edges between entities in the knowledge graph.

#### List Relationships

```
GET /api/relationships
```

Query parameters:
- `source_id` (optional): Filter by source entity ID
- `target_id` (optional): Filter by target entity ID
- `entity_id` (optional): Filter by either source or target entity ID
- `type` (optional): Filter by relationship type
- `limit` (optional): Maximum number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)
- `sort` (optional): Field to sort by (default: "created_at")
- `order` (optional): Sort order - "asc" or "desc" (default: "desc")

Response:
```json
{
  "success": true,
  "relationships": [
    {
      "id": "relationship_id",
      "source_id": "source_entity_id",
      "source_label": "Source Entity",
      "target_id": "target_entity_id",
      "target_label": "Target Entity",
      "relationship_type": "related_to",
      "created_at": "2023-01-01T12:00:00Z"
    },
    ...
  ],
  "pagination": {
    "total": 50,
    "offset": 0,
    "limit": 20,
    "next_offset": 20
  }
}
```

#### Get Relationship

```
GET /api/relationships/{relationship_id}
```

Response:
```json
{
  "success": true,
  "relationship": {
    "id": "relationship_id",
    "source_id": "source_entity_id",
    "source_label": "Source Entity",
    "source_type": "concept",
    "target_id": "target_entity_id",
    "target_label": "Target Entity",
    "target_type": "concept",
    "relationship_type": "related_to",
    "attributes": {
      "custom_field1": "value1",
      "custom_field2": "value2"
    },
    "created_at": "2023-01-01T12:00:00Z",
    "updated_at": "2023-01-02T12:00:00Z"
  }
}
```

#### Create Relationship

```
POST /api/relationships
```

Request body:
```json
{
  "source_id": "source_entity_id",
  "target_id": "target_entity_id",
  "relationship_type": "related_to",
  "attributes": {
    "custom_field1": "value1",
    "custom_field2": "value2"
  }
}
```

Response:
```json
{
  "success": true,
  "relationship": {
    "id": "new_relationship_id",
    "source_id": "source_entity_id",
    "source_label": "Source Entity",
    "target_id": "target_entity_id",
    "target_label": "Target Entity",
    "relationship_type": "related_to",
    "attributes": { ... },
    "created_at": "2023-01-01T12:00:00Z"
  }
}
```

#### Update Relationship

```
PUT /api/relationships/{relationship_id}
```

Request body (only include fields to update):
```json
{
  "relationship_type": "depends_on",
  "attributes": {
    "custom_field1": "new_value"
  }
}
```

Response:
```json
{
  "success": true,
  "relationship": {
    "id": "relationship_id",
    "source_id": "source_entity_id",
    "target_id": "target_entity_id",
    "relationship_type": "depends_on",
    "attributes": { ... },
    "updated_at": "2023-01-02T12:00:00Z"
  }
}
```

#### Delete Relationship

```
DELETE /api/relationships/{relationship_id}
```

Response:
```json
{
  "success": true,
  "message": "Relationship deleted successfully"
}
```

### Graph Operations

Graph operations provide specialized methods for working with the knowledge graph structure.

#### Find Paths

```
GET /api/graph/paths
```

Query parameters:
- `source_id` (required): Source entity ID
- `target_id` (required): Target entity ID
- `max_length` (optional): Maximum path length (default: 3)
- `relationship_types` (optional): Comma-separated list of relationship types to consider

Response:
```json
{
  "success": true,
  "paths": [
    [
      {
        "id": "source_id",
        "label": "Source Entity",
        "type": "concept",
        "relationship_to_next": "related_to"
      },
      {
        "id": "intermediate_id",
        "label": "Intermediate Entity",
        "type": "concept",
        "relationship_to_next": "contains"
      },
      {
        "id": "target_id",
        "label": "Target Entity",
        "type": "concept"
      }
    ],
    ...
  ]
}
```

#### Get Related Entities

```
GET /api/graph/related/{entity_id}
```

Query parameters:
- `relationship_types` (optional): Comma-separated list of relationship types to filter by

Response:
```json
{
  "success": true,
  "entity": {
    "id": "entity_id",
    "label": "Entity Label",
    "type": "concept"
  },
  "related": {
    "related_to": [
      {
        "id": "related_entity_id",
        "label": "Related Entity",
        "type": "concept",
        "direction": "outgoing"
      },
      ...
    ],
    "contains": [
      {
        "id": "contained_entity_id",
        "label": "Contained Entity",
        "type": "concept",
        "direction": "outgoing"
      },
      ...
    ],
    "inverse_part_of": [
      {
        "id": "parent_entity_id",
        "label": "Parent Entity",
        "type": "concept",
        "direction": "incoming"
      },
      ...
    ]
  }
}
```

#### Get Central Entities

```
GET /api/graph/central
```

Query parameters:
- `count` (optional): Number of entities to return (default: 10)
- `type` (optional): Filter by entity type

Response:
```json
{
  "success": true,
  "entities": [
    {
      "id": "entity_id",
      "label": "Central Entity",
      "type": "concept",
      "centrality": 0.85,
      "connections": 12
    },
    ...
  ]
}
```

#### Get Entity Types

```
GET /api/graph/entity-types
```

Response:
```json
{
  "success": true,
  "types": {
    "concept": 120,
    "person": 45,
    "domain": 15,
    "category": 10
  }
}
```

#### Get Relationship Types

```
GET /api/graph/relationship-types
```

Response:
```json
{
  "success": true,
  "types": {
    "related_to": 85,
    "contains": 62,
    "evolved_into": 34,
    "implemented_by": 28
  }
}
```

#### Get Graph Statistics

```
GET /api/graph/stats
```

Response:
```json
{
  "success": true,
  "stats": {
    "node_count": 190,
    "edge_count": 310,
    "entity_types": {
      "concept": 120,
      "person": 45,
      "domain": 15,
      "category": 10
    },
    "relationship_types": {
      "related_to": 85,
      "contains": 62,
      "evolved_into": 34,
      "implemented_by": 28
    },
    "central_entities": [
      {
        "id": "entity_id",
        "label": "Central Entity",
        "type": "concept",
        "centrality": 0.85,
        "connections": 12
      },
      ...
    ],
    "sections": 15,
    "subsections": 75
  }
}
```

### API Examples

#### Python Example: Finding Paths Between Concepts

```python
import requests
import json

BASE_URL = "http://localhost:5001/api"

def find_paths(source, target, max_length=3):
    url = f"{BASE_URL}/graph/paths"
    params = {
        "source_id": source,
        "target_id": target,
        "max_length": max_length
    }
    
    response = requests.get(url, params=params)
    return response.json()

# Find paths between "feedback_loops" and "neural_networks"
paths = find_paths("feedback_loops", "neural_networks")
if paths["success"]:
    for i, path in enumerate(paths["paths"]):
        print(f"Path {i+1}:")
        for node in path:
            print(f"  {node['label']}", end="")
            if "relationship_to_next" in node:
                print(f" --{node['relationship_to_next']}-->", end="")
            print()
        print()
else:
    print(f"Error: {paths['error']}")
```

#### JavaScript Example: Creating a New Entity with External URL

```javascript
async function createEntity() {
    const response = await fetch('http://localhost:5001/api/entities', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            "label": "Free Energy Principle",
            "type": "concept",
            "description": "A principle that states systems that minimize free energy will resist a natural tendency to disorder",
            "external_url": "https://example.com/free-energy-principle",
            "attributes": {
                "field": "neuroscience",
                "year_proposed": 2010
            }
        })
    });
    
    const data = await response.json();
    if (data.success) {
        console.log(`Created entity: ${data.entity.id}`);
        return data.entity;
    } else {
        console.error(`Error: ${data.error}`);
        return null;
    }
}
```

#### cURL Example: Creating a Relationship

```bash
curl -X POST http://localhost:5001/api/relationships \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "free_energy_principle",
    "target_id": "predictive_processing",
    "relationship_type": "related_to",
    "attributes": {
      "strength": "strong",
      "notes": "Both theories describe brain function as prediction-driven"
    }
  }'
```