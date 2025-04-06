# CYBERON (Cybernetic Ontology) Technical Architecture

**Table of Contents**

1.  [Overview](#overview)
2.  [Core loop data flow](#core-loop-data-flow)
    * [Interface for humans](#interface-for-humans)
    * [Interface for bots](#interface-for-bots)
    * [REST API](#rest-api)
3.  [Data model details](#data-model-details)
4.  [QueryEngine](#queryengine)
5.  [Flask web app (human interface) details](#flask-web-app-human-interface-details)
    * [UI Components](#ui-components)
    * [Core Views](#core-views)
6.  [MCP server/client details](#mcp-serverclient-details)
7.  [MCP Methods](#mcp-methods)
8.  [Handler System](#handler-system)
    * [Core Handlers](#core-handlers)
    * [Query Handlers](#query-handlers)
    * [Resource Handlers](#resource-handlers)
    * [Tool Handlers](#tool-handlers)
    * [Prompt Handlers](#prompt-handlers)
9.  [Resources System](#resources-system)
10. [Tools System](#tools-system)
11. [Prompts System](#prompts-system)
12. [REST API Details](#rest-api-details)

---

## 1. Overview <a name="overview"></a>

A junkyard of tools & interfaces wrapped around a graph engine.

## 2. Core loop data flow <a name="core-loop-data-flow"></a>

Start with unstructured text (research article, deep research report, your AI boyfriend's message history, etc)
Extract unstructured text into markdown intermediate format, consisting of categories and entities with defined attributes and relationships.
Parse markdown into directed graph (NetworkX),
New graph case --> save as node-link JSON file (break) Update graph case --> ...
Compare the input graph against the existing graph to produce a diff
Present diff to user for review, Reject --> Some rework process Accept --> Commit updated graph to file (or version control?)

### Interface for humans <a name="interface-for-humans"></a>

* Flask-based web app to visualize and explore knowledge graphs.
* Blueprints:
    * `main`: Core routes and query engine
    * `api`: RESTful endpoints
    * `visualization`: Graph visualization

### Interface for bots <a name="interface-for-bots"></a>

* Model Context Protocol (MCP) server+client allowing LLM / client access.
* STDIO transport by default, local communication only. Warning, no authentication / authorization / security effort is built into the MCP server based on the design intent of local use only.
* JSON-RPC 2.0 message format.
* LLM application runs client, which runs server, which accesses the graph model. (Server is not persistent.)
* There's also a named pipe transport for if we wanted a persistent server for some reason I guess.

### REST API <a name="rest-api"></a>

Simple API allowing flask interface and other internal tools to access the query engine. JSON structure, REST status conventions.
* Entity Endpoints: CRUD operations for entities (nodes)
* Relationship Endpoints: CRUD operations for relationships (edges)
* Graph Endpoints: Operations on the graph structure (paths, centrality, etc.)

## 3. Data model details <a name="data-model-details"></a>

## 4. QueryEngine <a name="queryengine"></a>

* Knowledge graph construction
* Entity and relationship queries
* Path finding
* Centrality analysis
* Concept evolution tracing

## 5. Flask web app (human interface) details <a name="flask-web-app-human-interface-details"></a>

### UI Components <a name="ui-components"></a>

* Template-Based UI: Jinja2 templates with TailwindCSS
* Interactive Visualization:
    * Force-directed graph (Force-Graph, D3.js)
    * Client-side filtering and node interaction
    * For detailed explanations, attributes may have links to external content.

### Core Views <a name="core-views"></a>

* Interactive visualization
* Concept browser
* There's some kind of explorer / search thing that isn't working well after data formats were reworked.

## 6. MCP server/client details <a name="mcp-serverclient-details"></a>

See MCP\_README.md for details on usage and formatting for requests and responses.

## 7. MCP Methods <a name="mcp-methods"></a>

* `initialize`: MCP connection initialization
* `cyberon/search`: Entity search
* `cyberon/entity`: Entity details
* `cyberon/paths`: Path finding
* `resources/list`: Resource listing
* `resources/read`: Resource reading
* `tools/list`: Tool listing
* `tools/execute`: Tool execution
* `prompts/list`: Prompt listing
* `prompts/get`: Prompt retrieval

## 8. Handler System <a name="handler-system"></a>

### Core Handlers <a name="core-handlers"></a>

* Initialization and capability negotiation

### Query Handlers <a name="query-handlers"></a>

* Entity search
* Information retrieval
* Path finding

### Resource Handlers <a name="resource-handlers"></a>

* Resource listing
* Templates
* Reading
* Subscriptions

### Tool Handlers <a name="tool-handlers"></a>

* Tool discovery
* Schema retrieval
* Execution

### Prompt Handlers <a name="prompt-handlers"></a>

* Prompt template management
* Generation

## 9. Resources System <a name="resources-system"></a>

* URI Scheme: `cyberon:///` for resource access
* Resource Types:
    * Entities
    * Relationships
    * Sections
    * Types
* Resource Templates: Dynamic URI construction

## 10. Tools System <a name="tools-system"></a>

* Tool Registry: Centralized registry with schemas
* Basic Tools:
    * Search
    * Entity analysis
    * Comparison
    * Central entities
* Advanced Tools:
    * Concept hierarchy
    * Related concepts
    * Evolution tracing
* Parameter Validation: JSON Schema

## 11. Prompts System <a name="prompts-system"></a>

* Prompt Templates: Natural language for ontology exploration
* Context Generation: Rich context for LLMs
* Specialized Prompts:
    * Entity analysis
    * Comparison
    * Hierarchy

## 12. REST API Details <a name="rest-api-details"></a>

* `/api/graph-data`: Graph nodes and edges
* `/api/entity/<entity_id>`: Entity details
* `/api/search`: Text search
* `/api/paths`: Path finding
* `/api/concepts/central`: Central concepts
* `/api/concepts/evolution`: Evolution chains