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
