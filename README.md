# Cyberon - Cybernetics Digital Garden

A Flask web application for exploring and visualizing cybernetics ontologies using knowledge graph technology.

## Features

- Upload and parse cybernetics ontology text files
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
│   │   └── query_engine.py  # Cybernetics query engine
│   ├── routes/              # Route blueprints
│   │   ├── api.py           # API endpoints
│   │   ├── main.py          # Main routes
│   │   └── visualization.py # Visualization routes
│   ├── static/              # Static files
│   │   ├── css/             # CSS files
│   │   ├── js/              # JavaScript files
│   │   └── libs/            # Third-party libraries
│   ├── templates/           # HTML templates
│   └── utils/               # Utility functions
│       └── ontology_parser.py # Ontology parsing utilities
├── data/                    # Data directory
├── instance/                # Instance-specific data
├── uploads/                 # Uploaded files
├── requirements.txt         # Dependencies
└── run.py                   # Application entry point
```

# Input file format
```Markdown
# Main Domain/Section

## Subsection
- Concept Name: Description of the concept
- Another Concept: Its description

## Key Figures
- Person Name: Description of the person
- Another Person: Their description

# Another Domain/Section

## Another Subsection
- Concept: Description
```


# Function signature for writing parsers
```python
def parse_ontology_file(input_file_path, output_json_path, format_type='default'):
    """
    Parse an ontology text file into a hierarchical structure and convert it to JSON for the Cybernetics Digital Garden application.
    
    Args:
        input_file_path (str): Path to the input ontology text file
        output_json_path (str): Path where the output JSON should be saved
        format_type (str): The format of the input file. Options:
            - 'markdown': Markdown formatted with headers and lists
            - 'json': Already in JSON but needs transformation to app's required schema?
    
    Returns:
        dict: The generated ontology data structure with 'structured_ontology' and 'knowledge_graph' keys
        
    Structured_ontology follows a hierarchical format:
    {
        "categories": [
            {
                "id": "unique_id",
                "title": "Category Title",
                "children": [
                    {
                        "id": "subcategory_id",
                        "title": "Subcategory Title",
                        "children": [...] or "type": "concept" for leaf nodes
                    },
                    ...
                ]
            },
            ...
        ]
    }
    
    Knowledge_graph represents relationships between entities:
    {
        "nodes": [
            {"id": "node_id", "label": "Node Label", "type": "concept|category|person|domain"},
            ...
        ],
        "edges": [
            {"source": "source_id", "target": "target_id", "label": "relationship_type"},
            ...
        ]
    }
    
    Raises:
        ValueError: If the format_type is not supported or input file cannot be parsed
        FileNotFoundError: If the input file doesn't exist
    """
    # Implementation would vary based on format_type
    
    # Helper functions would be needed for:
    # 1. Parsing different input formats
    # 2. Generating unique IDs (e.g., by slugifying titles)
    # 3. Building the hierarchical structure
    # 4. Converting the hierarchical structure to a knowledge graph
    
    # Return the complete structure
    return {
        "structured_ontology": {
            "categories": [...]
        },
        "knowledge_graph": {
            "nodes": [...],
            "edges": [...]
        }
    }
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NetworkX for graph analysis
- Flask for web framework
- vis.js for network visualization