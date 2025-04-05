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
