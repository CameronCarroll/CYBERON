# CYBERON (Cybernetic Ontology) Technical Architecture

## Overview

A junkyard of tools & interfaces wrapped around a graph engine.

### Core loop data flow:
1. Start with unstructured text (research article, deep research report, your AI boyfriend's message history, etc)
2. Extract unstructured text into markdown intermediate format, consisting of categories and entities with defined attributes and relationships.
3. Parse markdown into directed graph (NetworkX), 
4. New graph case --> save as node-link JSON file (break)
   Update graph case --> ...
5. Compare the input graph against the existing graph to produce a diff
6. Present diff to user for review,
    Reject --> Some rework process
    Accept --> Commit updated graph to file (or version control?)
 

### Interface for humans
- Flask-based web app to visualize and explore knowledge graphs.
- Blueprints:
  - `main`: Core routes and query engine
  - `api`: RESTful endpoints
  - `visualization`: Graph visualization

### Interface for bots
- Model Context Protocol (MCP) server+client allowing LLM / client access.
- STDIO transport by default, local communication only. **Warning, no authentication / authorization / security effort is built into the MCP server based on the design intent of local use only.** 
- JSON-RPC 2.0 message format.
- LLM application runs client, which runs server, which accesses the graph model. (Server is not persistent.)
- There's also a named pipe transport *for if we wanted a persistent server for some reason I guess.*

### REST API
Simple API allowing flask interface and other internal tools to access the query engine. JSON structure, REST status conventions.

- **Entity Endpoints:** CRUD operations for entities (nodes)
- **Relationship Endpoints:** CRUD operations for relationships (edges)
- **Graph Endpoints:** Operations on the graph structure (paths, centrality, etc.)

---------------------------------------------------------------------------


## Data model details

### QueryEngine
- Knowledge graph construction
- Entity and relationship queries
- Path finding
- Centrality analysis
- Concept evolution tracing

---------------------------------------------------------------------------

## Flask web app (human interface) details

### UI Components
- **Template-Based UI**: Jinja2 templates with TailwindCSS
- **Interactive Visualization**:
  - Force-directed graph (Force-Graph, D3.js)
  - Client-side filtering and node interaction
  - For detailed explanations, attributes may have links to external content.

### Core Views
- Interactive visualization
- Concept browser
- There's some kind of explorer / search thing that isn't working well after data formats were reworked.

---------------------------------------------------------------------------

## MCP server/client details
See `MCP_README.md` for details on usage and formatting for requests and responses.

### MCP Methods

1. `initialize`: MCP connection initialization
2. `cyberon/search`: Entity search
3. `cyberon/entity`: Entity details
4. `cyberon/paths`: Path finding
5. `resources/list`: Resource listing
6. `resources/read`: Resource reading
7. `tools/list`: Tool listing
8. `tools/execute`: Tool execution
9. `prompts/list`: Prompt listing
10. `prompts/get`: Prompt retrieval

### Handler System

1. **Core Handlers**
   - Initialization and capability negotiation

2. **Query Handlers**
   - Entity search
   - Information retrieval
   - Path finding

3. **Resource Handlers**
   - Resource listing
   - Templates
   - Reading
   - Subscriptions

4. **Tool Handlers**
   - Tool discovery
   - Schema retrieval
   - Execution

5. **Prompt Handlers**
   - Prompt template management
   - Generation

### Resources System

- **URI Scheme**: `cyberon:///` for resource access
- **Resource Types**:
  - Entities
  - Relationships
  - Sections
  - Types
- **Resource Templates**: Dynamic URI construction

### Tools System

- **Tool Registry**: Centralized registry with schemas
- **Basic Tools**:
  - Search
  - Entity analysis
  - Comparison
  - Central entities
- **Advanced Tools**:
  - Concept hierarchy
  - Related concepts
  - Evolution tracing
- **Parameter Validation**: JSON Schema

### Prompts System

- **Prompt Templates**: Natural language for ontology exploration
- **Context Generation**: Rich context for LLMs
- **Specialized Prompts**:
  - Entity analysis
  - Comparison
  - Hierarchy

---------------------------------------------------------------------------

## REST API Details

- `/api/graph-data`: Graph nodes and edges
- `/api/entity/<entity_id>`: Entity details
- `/api/search`: Text search
- `/api/paths`: Path finding
- `/api/concepts/central`: Central concepts
- `/api/concepts/evolution`: Evolution chains

---------------------------------------------------------------------------




