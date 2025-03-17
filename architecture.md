I'll create a concise technical architecture summary for the cybernetics digital garden Flask application.

# Technical Architecture: Cybernetics Digital Garden

## Overview
This is a Flask-based web application that provides interactive visualization and exploration of cybernetics concepts using knowledge graph technology. The system allows users to upload ontology data, visualize relationships between concepts, and explore connections through various interfaces.

## Core Architecture

### Application Structure
- **Flask Application Factory Pattern**: Uses a modular structure with blueprints for separation of concerns
- **Blueprint Organization**:
  - `main`: Core routes and query engine initialization
  - `api`: RESTful endpoints for data retrieval
  - `visualization`: Graph visualization routes

### Data Processing Pipeline
1. **Ontology Parsing**: Text files are processed via `ontology_parser.py` which extracts structured information, including external URL references
2. **Knowledge Graph Construction**: Creates nodes (concepts, people, domains) with optional external URLs and edges (relationships)
3. **NetworkX Integration**: Graph is stored as a directed graph (`nx.DiGraph`) for analysis

### Query Engine
The `CyberneticsQueryEngine` class provides core functionality:
- Knowledge graph construction from JSON data
- Entity and relationship queries
- Path finding between concepts
- Centrality analysis for identifying key concepts
- Concept evolution tracing

### Frontend Architecture
- **Template-Based UI**: Uses Jinja2 templates with TailwindCSS
- **Interactive Visualizations**: 
  - Force-directed graph using Force-Graph library and D3.js
  - Client-side filtering and node interaction
  - External content linking for nodes with external_url field
- **Core Views**:
  - Ontology visualization (network graph)
  - Concept explorer (search, connections, evolution chains)
  - Structured ontology browser
  - External content access through node links

## Data Flow

1. User uploads ontology text file
2. Server processes file into structured JSON using `extract_text_to_json()`
3. JSON is loaded into `CyberneticsQueryEngine`
4. API endpoints provide graph data for visualization
5. Client-side JavaScript renders interactive visualizations

## Technical Components

- **Backend**: Python 3 with Flask
- **Graph Analysis**: NetworkX library
- **Frontend**: HTML/CSS with TailwindCSS, JavaScript with D3.js
- **Visualization**: Force-Graph for network visualization
- **Testing**: Pytest with API mocking

## API Endpoints

- `/api/graph-data`: Graph nodes and edges for visualization
- `/api/entity/<entity_id>`: Entity details with relationships
- `/api/search`: Text search across entities
- `/api/paths`: Path finding between entities
- `/api/concepts/central`: Central concept identification
- `/api/concepts/evolution`: Evolution chains of concepts

This architecture provides a modular, extensible framework for exploring complex knowledge domains through interactive visualizations and structured data navigation.