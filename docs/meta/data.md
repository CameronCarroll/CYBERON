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
