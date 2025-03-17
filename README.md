# Cyberon - Cybernetics Digital Garden

A Flask web application for exploring and visualizing knowledge ontologies using graph technology. Originally designed for cybernetics, but adaptable to any domain knowledge structure.

## Features

- Upload and parse ontology text files in markdown format
- Interactive knowledge graph visualization
- Search for concepts and entities
- Explore connections between concepts
- Find paths between entities
- Analyze concept hierarchies and evolution

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cyberon.git
cd cyberon
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
python run.py
```

2. Open your web browser and navigate to `http://localhost:5000`

3. Upload an ontology text file to begin exploring

## Creating Your Own Ontology

### Markdown Format

The system accepts markdown-formatted ontology files with a specific structure:

```markdown
# Main Section Title

## Subsection Title
- Concept Name: Description of the concept
- Another Concept: Its description

## Key Figures 
- Person Name: Description of the person
- Another Person: Their description

# Another Section Title

## Another Subsection
- Concept: Description
```

**Key points:**
- Use H1 (`#`) for main sections
- Use H2 (`##`) for subsections 
- Use bullet points (`-`) for concepts or entities
- Add a colon (`:`) after each entity name to provide a description

### System Behavior
- Entities in subsections containing "Key Figures", "People", or "Person" are categorized as people
- All other entities are categorized as concepts
- Entities within the same subsection are automatically related to each other

## Data Structure

The system processes markdown files into a JSON structure with two main components:

### 1. Structured Ontology

```json
{
  "section_id": {
    "title": "Section Title",
    "subsections": {
      "Subsection Name": [
        {
          "name": "Entity Name",
          "description": "Entity Description"
        },
        {
          "name": "Another Entity",
          "description": "Another Description"
        }
      ],
      "Another Subsection": [
        ...
      ]
    }
  },
  "another_section_id": {
    ...
  }
}
```

### 2. Knowledge Graph

```json
{
  "nodes": [
    {"id": "entity_id", "label": "Entity Name", "type": "concept|person|category"},
    ...
  ],
  "edges": [
    {"source": "source_id", "target": "target_id", "label": "relationship_type"},
    ...
  ]
}
```

## Customizing for Other Domains

While Cyberon was built for cybernetics, you can use it for any domain knowledge by:

1. **Creating your own ontology file**:
   - Structure your markdown file as shown above
   - Use consistent naming patterns for your entities
   - Group related concepts in the same subsections
   - Use descriptive section and subsection titles

2. **Modifying classification rules** (optional):
   - Edit `extract_entities()` in `app/utils/ontology_parser.py` to customize entity type detection based on your domain

3. **Enhancing relationship detection** (optional):
   - Edit `convert_to_knowledge_graph()` in `app/utils/ontology_parser.py` to add custom relationship types or detection rules

## Example: Creating a Literature Ontology

```markdown
# Victorian Literature

## Major Authors
- Charles Dickens: English novelist known for Oliver Twist and Great Expectations
- George Eliot: Pen name of Mary Ann Evans, author of Middlemarch
- Thomas Hardy: English novelist and poet known for Far from the Madding Crowd

## Literary Movements
- Realism: Attempted to represent subject matter truthfully
- Gothic Fiction: Genre combining fiction, horror and Romanticism
- Naturalism: Literary movement seeking to replicate everyday reality

# Modernist Literature

## Key Figures
- Virginia Woolf: British author known for Mrs Dalloway and To The Lighthouse
- James Joyce: Irish novelist and poet, author of Ulysses
- T.S. Eliot: American-born British poet known for The Waste Land

## Techniques
- Stream of Consciousness: Narrative mode depicting point-by-point thoughts of characters
- Unreliable Narrator: Narrator whose credibility is compromised
- Fragmentation: Breaking narrative into pieces to reflect modern experience
```

## Testing

To run the tests:

```bash
pytest
```

To run a specific test file:

```bash
pytest app/tests/test_api.py
```

To run tests with a specific marker:

```bash
pytest -m api
```

## Project Structure

```
cyberon/
├── app/                     # Application package
│   ├── __init__.py          # Application factory
│   ├── models/              # Data models
│   │   └── query_engine.py  # Ontology query engine
│   ├── routes/              # Route blueprints
│   │   ├── api.py           # API endpoints
│   │   ├── main.py          # Main routes
│   │   └── visualization.py # Visualization routes
│   ├── static/              # Static files
│   ├── templates/           # HTML templates
│   └── utils/               # Utility functions
│       └── ontology_parser.py # Ontology parsing utilities
├── data/                    # Data directory
├── instance/                # Instance-specific data
├── uploads/                 # Uploaded files
├── requirements.txt         # Dependencies
└── run.py                   # Application entry point
```

## API Endpoints

- `/api/graph-data`: Graph nodes and edges for visualization
- `/api/entity/<entity_id>`: Entity details with relationships
- `/api/search`: Text search across entities
- `/api/paths`: Path finding between entities
- `/api/concepts/central`: Central concept identification
- `/api/concepts/evolution`: Evolution chains of concepts

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NetworkX for graph analysis
- Flask for web framework
- vis.js and D3.js for network visualization