# CYBERON API and Protocol Interfaces

## REST API Endpoints
- Graph Data API: Provides graph nodes and edges for visualization
- Entity API: CRUD operations for ontology entities
- Relationship API: CRUD operations for entity relationships
- Search API: Text search functionality for entities
- Path Finding API: Discovers paths between entities
- Central Concepts API: Identifies central concepts in the ontology
- Evolution API: Traces concept evolution chains
- Upload API: Handles ontology file uploads

## MCP Protocol Methods
- Initialize: Establishes MCP connection and negotiates capabilities
- Entity Search: Finds entities matching search criteria
- Entity Details: Retrieves detailed information about entities
- Path Finding: Discovers paths between entities
- Resource Listing: Enumerates available resources
- Resource Reading: Retrieves content from resources
- Tool Listing: Lists available tools and their schemas
- Tool Execution: Executes tools with provided parameters
- Prompt Listing: Lists available prompt templates
- Prompt Generation: Generates prompts from templates

## API Request Formats
- JSON Requests: Standard format for REST API requests
- Query Parameters: URL parameters for GET requests
- JSON-RPC 2.0: Message format for MCP protocol
- Form Data: Multipart form data for file uploads

## API Response Formats
- JSON Responses: Standard format for REST API responses
- Graph Format: Nodes and edges for visualization
- Entity Format: Detailed entity information
- Path Format: Sequences of connected entities
- Error Format: Standardized error responses
- JSON-RPC 2.0: Response format for MCP protocol

## API Authentication and Security
- Rate Limiting: Controls request frequency
- IP Whitelisting: Exempts specific IPs from rate limiting
- Error Handling: Standardized error responses
- Input Validation: Validates request parameters

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

# CYBERON Data Processing Pipeline

## Ontology Processing Flow
- Markdown Input: Raw markdown files with structured ontology content
- Parsing Stage: Extraction of structured data from markdown
- Knowledge Graph Construction: Building graph from structured data
- Storage: JSON serialization of structured ontology and knowledge graph
- Query Engine Loading: Loading data into the query engine for access

## Ontology Parser Components
- Markdown Parser: Processes markdown text into structured format
- Entity Extractor: Identifies entities and their types
- Relationship Builder: Creates relationships between entities
- Graph Converter: Transforms structured data into knowledge graph
- JSON Serializer: Saves processed data to JSON format

## Knowledge Graph Structure
- Nodes: Entities in the ontology (concepts, people, categories)
- Edges: Relationships between entities
- Node Attributes: Properties of entities (type, label, external URL)
- Edge Attributes: Properties of relationships (label)
- Graph Hierarchy: Section > Subsection > Entity structure

## Query Engine Operations
- Graph Building: Constructs NetworkX graph from knowledge graph data
- Entity Queries: Retrieves detailed information about entities
- Path Finding: Discovers paths between entities
- Connection Analysis: Finds entities connected within a distance
- Centrality Analysis: Identifies central concepts in the ontology
- Search: Finds entities matching search criteria

## Data Transformation
- Text to Structure: Markdown to structured dictionary
- Structure to Graph: Dictionary to nodes and edges
- Graph to NetworkX: JSON graph to NetworkX object
- Query to Results: Graph queries to structured results

# CYBERON Flask Application Structure

## Core Flask Components
- Application Factory: Creates and configures the Flask application
- Blueprints: Modular components for different application features
- Routes: URL handlers for web interface and API endpoints
- Templates: Jinja2 templates for rendering HTML pages
- Static Files: CSS, JavaScript, and other static assets

## Blueprint Organization
- Main Blueprint: Core routes and query engine initialization
- API Blueprint: RESTful API endpoints for data access
- Visualization Blueprint: Graph visualization routes
- Entities Blueprint: CRUD operations for ontology entities
- Relationships Blueprint: CRUD operations for entity relationships
- Graph Blueprint: Graph-specific API endpoints

## Route Handlers
- Index Route: Entry point to the application
- Upload Route: Handles ontology file uploads
- Search Route: Provides entity search functionality
- Entity Route: Displays entity details
- Graph Data Route: Provides graph data for visualization
- Path Finding Route: Finds paths between entities
- Central Concepts Route: Identifies central concepts in the ontology

## Middleware Components
- Rate Limiter: Controls request frequency
- Error Handlers: Manages application errors
- Request Preprocessing: Prepares requests for handling
- Response Formatting: Standardizes API responses

## Flask Extensions
- Flask-Limiter: Rate limiting functionality
- Jinja2: Template engine for HTML rendering
- Werkzeug: WSGI utilities for request handling

# CYBERON MCP Server Components

## Core MCP Architecture
- Server: Main MCP server implementation handling client connections
- Transport Layer: Communication interfaces for different protocols
- Handler System: Specialized handlers for different request types
- Resources System: Resource management and access via URIs
- Tools System: Tool discovery and execution framework
- Prompts System: Template-based prompt management

## Transport Layer
- Base Transport: Abstract base class for all transport implementations
- STDIO Transport: Standard input/output communication channel
- Named Pipe Transport: Communication via named pipes
- Transport Selection: Runtime selection of appropriate transport

## Handler System
- Core Handlers: Basic protocol operations and initialization
- Query Handlers: Entity search and information retrieval
- Resource Handlers: Resource access and management
- Tool Handlers: Tool discovery and execution
- Prompt Handlers: Prompt template management

## Resources System
- URI Scheme: cyberon:/// protocol for resource identification
- Resource Types: Entities, relationships, sections, types
- Resource Templates: Dynamic URI construction patterns
- Resource Reading: Content retrieval from resources
- Resource Listing: Directory-like resource enumeration

## Tools System
- Tool Registry: Central registry of available tools
- Tool Schema: JSON Schema definitions for tool parameters
- Basic Tools: Search, entity analysis, comparison tools
- Advanced Tools: Concept hierarchy, evolution tracing tools
- Parameter Validation: Input validation using JSON Schema

## Prompts System
- Prompt Templates: Natural language templates for ontology exploration
- Context Generation: Rich context creation for LLMs
- Specialized Prompts: Entity analysis, comparison, hierarchy prompts
- Template Variables: Dynamic variable substitution in templates
