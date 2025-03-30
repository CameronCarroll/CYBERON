# CYBERON - Cybernetic Ontology

Human interface: A Flask web application for exploring and visualizing knowledge ontologies using graph technology. Originally designed for cybernetics, but adaptable to any domain knowledge structure. Supports linking knowledge graph nodes to external content via the external_url field.

LLM interface: MCP server (Python) and client (Crystal lang)

Graph & query engine underneath for managing, querying and reasoning over structured ontologies.

## Documentation

- See API reference at `/API_README.md`

## Features

- Upload and parse ontology text files in markdown format
- Interactive knowledge graph visualization
- Search for concepts and entities
- Explore connections between concepts
- Find paths between entities
- Analyze concept hierarchies and evolution
- Link knowledge graph nodes to external content via URLs

## Model Context Protocol (MCP) Server

This application includes a Model Context Protocol server that allows LLMs and other clients to interact with the cybernetics ontology through a standardized protocol. The MCP server provides:

- Entity search and information retrieval
- Path finding between concepts
- Resource access via URIs
- Tool execution for ontology analysis
- Prompt templates for natural language interaction

# CYBERON Setup Instructions

## Prerequisites
- Python 3.8 or higher
- Flask and dependencies (see requirements.txt)
- `sudo` access for systemd service installation

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/cyberon.git
   cd cyberon
   ```

2. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create the directory for named pipes:
   ```bash
   sudo mkdir -p /run/cyberon
   ```

4. Create the named pipes:
   ```bash
   sudo mkfifo /run/cyberon/mcp_in.pipe
   sudo mkfifo /run/cyberon/mcp_out.pipe
   ```

5. Set appropriate permissions (replace `yourusername` with your actual username):
   ```bash
   sudo chown yourusername:yourusername /run/cyberon/mcp_in.pipe
   sudo chown yourusername:yourusername /run/cyberon/mcp_out.pipe
   sudo chmod 660 /run/cyberon/mcp_in.pipe
   sudo chmod 660 /run/cyberon/mcp_out.pipe
   ```

6. Create the systemd service file:
   ```bash
   sudo nano /etc/systemd/system/cyberon-mcp.service
   ```

7. Add the following content to the service file (adjust paths and username as needed):
   ```
   [Unit]
   Description=CYBERON MCP Server Stdio
   After=network.target
   
   [Service]
   Type=simple
   User=yourusername
   Group=yourusername
   WorkingDirectory=/path/to/cyberon/
   ExecStart=/bin/sh -c 'exec /usr/bin/python /path/to/cyberon/mcp_server.py --data-file=/path/to/cyberon/data_template.json < /run/cyberon/mcp_in.pipe > /run/cyberon/mcp_out.pipe'
   Restart=on-failure
   RestartSec=5
   StandardError=journal
   
   [Install]
   WantedBy=multi-user.target
   ```

8. Reload systemd, enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable cyberon-mcp.service
   sudo systemctl start cyberon-mcp.service
   ```

9. Verify the service is running:
   ```bash
   sudo systemctl status cyberon-mcp.service
   ```

## Using the Web Interface

1. Start the Flask web server:
   ```bash
   python run.py
   ```

2. Open your browser and navigate to http://localhost:5001

## Using the MCP Client

The MCP client communicates with the server through the named pipes:

```bash
python app/mcp/client.py
```

For testing or debugging pipe communication, you can use the simple debug client:

```bash
python app/mcp/simple_client.py
```

## Troubleshooting

- **Service won't start**: Check permissions on the named pipes and verify paths in the systemd service file.
- **Permission denied**: Ensure the pipes have correct ownership and permissions for your user.
- **Communication errors**: Verify both pipes exist and the service is running.

If you encounter issues with the named pipes, you can check the system journal:

```bash
journalctl -u cyberon-mcp.service -f
```

## Additional Notes

- The named pipes must be created before starting the service
- If you change the location of the named pipes, update both the systemd service file and any client configurations
- For persistent named pipes across reboots, consider adding their creation to a system startup script

## Creating Your Own Ontology

### Markdown Format

The system accepts markdown-formatted ontology files with a specific structure:

```markdown
# Main Section Title

## Subsection Title
- Concept Name: Description of the concept
- Another Concept [url:/path/to/external-content.html]: Its description with external link
- Yet Another Concept: Description without external link

## Key Figures 
- Person Name: Description of the person
- Another Person [url:/people/person-page.html]: Description with external link

# Another Section Title

## Another Subsection
- Concept: Description
```

**Key points:**
- Use H1 (`#`) for main sections
- Use H2 (`##`) for subsections 
- Use bullet points (`-`) for concepts or entities
- Add a colon (`:`) after each entity name to provide a description
- Optionally add `[url:/path/to/resource.html]` before the colon to link to external content

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
    {"id": "entity_id", "label": "Entity Name", "type": "concept|person|category", "external_url": "/optional/path/to/resource.html"},
    {"id": "another_entity", "label": "Another Entity", "type": "concept|person|category"},
    ...
  ],
  "edges": [
    {"source": "source_id", "target": "target_id", "label": "relationship_type"},
    ...
  ]
}
```

The `external_url` field is optional and only included when an entity has an associated external resource.

## Customizing for Other Domains

While Cyberon was built for cybernetics, you can adapt it to any domain knowledge graph:

### 1. Customizing Entity Type Detection

The default parser classifies entities as either "person" or "concept" based on subsection names. To add custom entity types:

```python
# In app/utils/ontology_parser.py
def extract_entities(structured_ontology: Dict):
    people = set()
    concepts = set()
    literary_works = set()  # New entity type
    domains = {}
    
    # Process each section
    for section_id, section_data in structured_ontology.items():
        section_title = section_data["title"]
        
        # Process each subsection
        for subsection_name, items in section_data["subsections"].items():
            # Create a domain entry
            domain_name = f"{section_title} - {subsection_name}"
            domains[domain_name] = items
            
            # Categorize items based on subsection name patterns
            if any(term in subsection_name.lower() for term in 
                  ["key figures", "people", "person", "authors", "poets"]):
                # Items in these subsections are people
                for item in items:
                    people.add(item["name"])
            elif any(term in subsection_name.lower() for term in 
                    ["works", "novels", "poems", "publications"]):
                # Items in these subsections are literary works
                for item in items:
                    literary_works.add(item["name"])
            else:
                # All other items are concepts
                for item in items:
                    concepts.add(item["name"])
    
    return people, concepts, literary_works, domains
```

Then update `convert_to_knowledge_graph()` to use your new entity type:

```python
# Determine item type
if item_name in people:
    item_type = "person"
elif item_name in literary_works:
    item_type = "literary_work"
else:
    item_type = "concept"
```

### 2. Adding Custom Relationship Types

The default system creates generic relationships like "contains" and "includes". Here's how to add domain-specific relationships:

```python
# In convert_to_knowledge_graph()
# After adding basic section-subsection-item relationships

# Add author-to-work relationships
for section_id, section_data in structured_ontology.items():
    author_subsection = None
    works_subsection = None
    
    # Find author and works subsections in the same section
    for subsection_name, items in section_data["subsections"].items():
        if any(term in subsection_name.lower() for term in ["authors", "poets", "key figures"]):
            author_subsection = subsection_name
        elif any(term in subsection_name.lower() for term in ["works", "novels", "poems"]):
            works_subsection = subsection_name
    
    # Create authored_by relationships if both subsections exist
    if author_subsection and works_subsection:
        for author_item in section_data["subsections"][author_subsection]:
            author_id = make_id(author_item["name"])
            for work_item in section_data["subsections"][works_subsection]:
                work_id = make_id(work_item["name"])
                
                # Create "authored_by" relationship
                edges.append({
                    "source": work_id,
                    "target": author_id,
                    "label": "authored_by"
                })
```

### 3. Implementing Relationship Detection Rules

You can implement more sophisticated relationship detection using NLP-style pattern matching:

```python
# Add relationships based on description text analysis
for section_id, section_data in structured_ontology.items():
    for subsection_name, items in section_data["subsections"].items():
        for item in items:
            item_id = make_id(item["name"])
            description = item["description"].lower()
            
            # Check for influence relationships in descriptions
            for other_item in items:
                if item == other_item:
                    continue
                    
                other_id = make_id(other_item["name"])
                
                # Look for name mentions in descriptions
                if other_item["name"].lower() in description:
                    # Check for specific relationship patterns
                    if any(pattern in description for pattern in 
                          ["influence", "inspired", "based on"]):
                        edges.append({
                            "source": item_id,
                            "target": other_id,
                            "label": "influenced_by"
                        })
                    elif any(pattern in description for pattern in 
                            ["critique", "criticize", "response to"]):
                        edges.append({
                            "source": item_id,
                            "target": other_id,
                            "label": "critiques"
                        })
```

### Example: Literary Movement Ontology

Here's a complete example using these customizations:

```markdown
# Romantic Period

## Key Authors
- William Wordsworth: English Romantic poet who helped launch the Romantic Age with the publication of Lyrical Ballads
- Samuel Taylor Coleridge: English poet and critic, influenced by William Wordsworth and known for supernatural poems
- Lord Byron: Leading figure of the Romantic movement, known for his satirical work "Don Juan"

## Major Works
- Lyrical Ballads: Collection of poems by Wordsworth and Coleridge that marked the beginning of the English Romantic movement
- The Prelude: Wordsworth's autobiographical poem, considered his masterpiece
- Don Juan: Byron's satirical epic poem that critiques social and sexual conventions

## Prominent Themes
- Nature: Central importance in Romantic literature as a source of inspiration and spiritual truth
- Imagination: Valued over reason and associated with creativity and spiritual truth
- Individualism: Focus on the individual and inner experience

# Victorian Period

## Notable Authors
- Charles Dickens: English writer known for creating some of literature's most memorable characters
- George Eliot: Pen name of Mary Ann Evans, known for realistic novels that examine social issues
- Thomas Hardy: English novelist and poet whose works were influenced by Romanticism but critique Victorian society

## Significant Works
- Great Expectations: Novel by Charles Dickens that depicts the personal growth of an orphan named Pip
- Middlemarch: George Eliot's study of provincial life, considered one of the greatest novels in English
- Tess of the d'Urbervilles: Thomas Hardy's novel that critiques Victorian notions of social and sexual purity
```

When parsed with your customized code, this would produce nodes of types "person", "literary_work", and "concept", with relationships including basic ones like "contains" and "includes", plus domain-specific ones like "authored_by", "influenced_by", and "critiques".

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