# CYBERON Application Architecture

## Core Components
- Flask Application: Web interface for human interaction with the ontology
- MCP Server: Protocol server for LLM interaction with the ontology
- Query Engine: Backend for managing and querying the knowledge graph
- Ontology Parser: Processes markdown files into structured knowledge graphs
- Data Storage: JSON-based storage for ontology and graph data

## Application Layers
- Presentation Layer: Flask routes and templates for web UI
- API Layer: REST endpoints and MCP protocol handlers
- Business Logic Layer: Query engine and ontology processing
- Data Layer: JSON file storage and NetworkX graph representation

## Integration Points
- Flask to Query Engine: Main application uses query engine for data access
- MCP Server to Query Engine: Protocol server uses query engine for data operations
- Ontology Parser to Data Storage: Parser transforms markdown to JSON data
- API to Query Engine: REST endpoints use query engine for data retrieval
- MCP Handlers to Resources: Protocol handlers access ontology resources

## Deployment Components
- Web Server: Flask application serving web UI
- MCP Server: Standalone or integrated server for LLM access
- Named Pipes: Communication channel for external MCP clients
- File System: Storage for ontology data and uploaded files
