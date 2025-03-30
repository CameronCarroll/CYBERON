# Cybernetics Digital Garden - Technical Architecture

## Overview

A Flask-based web application for interactive visualization and exploration of cybernetics concepts using a knowledge graph. It includes a Model Context Protocol (MCP) server for standardized API access for LLMs and other clients.

## Core Architecture

### Application Structure

#### Flask Application Factory Pattern
- Modular structure with blueprints
- Blueprints:
  - `main`: Core routes and query engine
  - `api`: RESTful endpoints
  - `visualization`: Graph visualization

#### MCP Server Integration
- Core MCP server integrated with Flask
- JSON-RPC 2.0 message format

### Data Processing Pipeline

#### Ontology Parsing
- `ontology_parser.py` extracts structured information and URLs
- Knowledge Graph Construction:
  - Nodes (concepts, people, domains)
  - Edges (relationships)
- NetworkX Integration: `nx.DiGraph` for graph analysis

### Query Engine

#### CyberneticsQueryEngine
- Knowledge graph construction
- Entity and relationship queries
- Path finding
- Centrality analysis
- Concept evolution tracing

## MCP Server Architecture

### Transport Layer

- **Transport Interface**: Abstract communication protocol
- **STDIO Transport**: Standard input/output communication
- **Message Handling**: JSON-RPC 2.0 parsing and formatting

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

## Frontend Architecture

### UI Components
- **Template-Based UI**: Jinja2 templates with TailwindCSS
- **Interactive Visualizations**:
  - Force-directed graph (Force-Graph, D3.js)
  - Client-side filtering and node interaction
  - External content linking

### Core Views
- Ontology visualization
- Concept explorer
- Structured ontology browser
- External content access

## Data Flow

1. User uploads ontology or LLM connects via MCP
2. Server processes file to JSON using `extract_text_to_json()`
3. JSON loaded into CyberneticsQueryEngine
4. API endpoints provide graph data (web UI)
5. MCP handlers provide ontology access (LLMs/clients)
6. Client-side JavaScript renders visualizations (web UI)
7. MCP clients process responses (LLM integration)

## API and Protocol Interfaces

### REST API Endpoints

- `/api/graph-data`: Graph nodes and edges
- `/api/entity/<entity_id>`: Entity details
- `/api/search`: Text search
- `/api/paths`: Path finding
- `/api/concepts/central`: Central concepts
- `/api/concepts/evolution`: Evolution chains

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