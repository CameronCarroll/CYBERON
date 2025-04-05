# CYBERON - Cybernetic Ontology

Human interface: A Flask web application for exploring and visualizing knowledge ontologies using graph technology. Originally designed for cybernetics, but adaptable to any domain knowledge structure. Supports associating attributes within the ontology to external URLs, making them accessible in the knowledge graph.

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
- Associate attributes within the ontology to external URLs, making them accessible in the knowledge graph

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
   git clone [https://github.com/CameronCarroll/cyberon.git](https://github.com/CameronCarroll/cyberon.git)
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

The system processes markdown-formatted ontology files adhering to the following structure. Each file should represent a distinct knowledge domain.

```Markdown
# Section Name

# Section Name defines a top-level category within the ontology.
# All entities belong to the most recently defined section.
# Lines starting with '##' are currently ignored by the parser.

- Entity: EntityName1
  # Defines a new entity within the current section. Must start with '- Entity:'.
  Description: A brief description of this entity.
  # Optional: Provides a human-readable description.
  Type: EntityType
  # Optional: Specifies the classification of the entity (e.g., Species, Organ, Concept, Person).
  Attributes:
    # Optional: Marks the beginning of the attribute list for this entity.
    - Attribute: AttributeName1
      # Defines an attribute. Must start with '- Attribute:'.
      Value: Some Value
      # Provides the value for the *immediately preceding* '- Attribute:'. Required if attribute defined.
    - Attribute: AttributeName2 [url:/path/to/resource]
      # Defines an attribute with an associated external URL.
      Value: Another Value
      # Provides the value for AttributeName2.
  Relationships:
    # Optional: Marks the beginning of the relationship list for this entity.
    - Relationship: relationship_type_1
      # Defines a relationship type originating from EntityName1. Must start with '- Relationship:'.
      Target: TargetEntityName1
      # Specifies the target entity for the *immediately preceding* '- Relationship:'. Required if relationship defined.
      # Inline comments after the target name (e.g., Target: TargetEntityName1 # comment) are ignored.
    - Relationship: relationship_type_2
      Target: TargetEntityName2

- Entity: EntityName2
  Description: Another entity.
  Type: AnotherType
  # This entity has no explicitly defined attributes or relationships in this example.

# Another Section Name

# Entities defined below will belong to "Another Section Name".

- Entity: TargetEntityName1
  Description: The target of the first relationship from EntityName1.
  Type: TargetType

- Entity: TargetEntityName2
  Description: The target of the second relationship from EntityName1.
  Type: TargetType
```

### Key Syntax Points

#### Sections:

- Use H1 (# Section Name) to define top-level categories.
- Entities belong to the last defined section.
- ## headings are ignored.

#### Entities:

- Define entities using a bullet point followed by `Entity:` and the entity name (e.g., `- Entity: EntityName`).

##### Entity Properties:

- Define properties directly under the `- Entity:` line (indentation helps readability but is not strictly enforced beyond line order):
  - `Description:` Text (Optional description)
  - `Type:` Text (Optional type classification)

#### Attributes Block:

- Start with `Attributes:`.
- List attributes using `- Attribute: AttributeName`.
  - Optionally include `[url:/path/...]` at the end of the `- Attribute:` line (before any potential newline) to associate a URL.
- Provide the attribute's value on the next line using `Value:` AttributeValue.

  **Important:** Each `- Attribute:` must be immediately followed by a `Value:`.

#### Relationships Block:

- Start with `Relationships:`.
- Define relationships using `- Relationship: relationship_type`.
- Specify the target entity on the next line using `Target:` TargetEntityName.
  - Inline comments (`# ...`) after the target name are stripped.

  **Important:** Each `- Relationship:` must be immediately followed by a `Target:`.

#### Order Matters:

- `Value:` must immediately follow the `- Attribute:` it belongs to.
- `Target:` must immediately follow the `- Relationship:` it belongs to.
- Attributes must be under an `Attributes:` heading.
- Relationships must be under a `Relationships:` heading.

### System Behavior (Based on Parser Logic)

#### Structure:

- The final output organizes entities under the section (#) they were defined in.

#### Entity Typing:

- An entity's type (e.g., "Person", "Concept", "Species") is determined only by the value provided in its `Type:` field. There is no automatic inference based on section names.

#### Relationships:

- Relationships between entities are created only if explicitly defined using the `Relationships:` block, `- Relationship:` type, and `Target:` name syntax. There are no automatic relationships created based on co-location within the file.

#### IDs:

- Unique IDs for nodes and attributes in the knowledge graph are generated automatically by lowercasing names and replacing non-alphanumeric characters with underscores (e.g., "Average Height" becomes `average_height`).

---

## Data Output: Knowledge Graph

The system processes the markdown ontology into a standard knowledge graph format represented in JSON. This JSON contains two main keys: `nodes` and `edges`.

```json
{
  "nodes": [
    {
      "id": "entityname1",
      "label": "EntityName1",
      "type": "EntityType",
      "description": "A brief description of this entity.",
      "attributename1": "Some Value",
      "attributename2": "Another Value",
      "attributename2_url": "/path/to/resource"
    },
    {
      "id": "entityname2",
      "label": "EntityName2",
      "type": "AnotherType",
      "description": "Another entity."
    },
    {
      "id": "targetentityname1",
      "label": "TargetEntityName1",
      "type": "TargetType",
      "description": "The target of the first relationship from EntityName1."
    },
    {
       "id": "targetentityname2",
       "label": "TargetEntityName2",
       "type": "TargetType",
       "description": "The target of the second relationship from EntityName1."
    }
  ],
  "edges": [
    {
      "source": "entityname1",
      "target": "targetentityname1",
      "label": "relationship_type_1"
    },
    {
      "source": "entityname1",
      "target": "targetentityname2",
      "label": "relationship_type_2"
    }
  ]
}
```

**Explanation:**

* **`nodes`**: An array of objects, where each object represents an entity from the markdown file.
    * `id`: A lower-case, underscore-separated unique identifier generated from the entity name.
    * `label`: The original entity name as defined in the markdown (`- Entity: EntityName`).
    * `type`: The entity type specified using the `Type:` field in the markdown.
    * `description`: The description provided using the `Description:` field.
    * *Attributes*: Attributes defined under the `Attributes:` block become direct key-value pairs on the node object. The key is the generated ID for the attribute name (e.g., `attributename1`).
    * *Attribute URLs*: If an attribute in the markdown had a `[url:/...]` associated with it, an additional field is added to the node with `_url` appended to the attribute ID key (e.g., `attributename2_url`).
* **`edges`**: An array of objects representing the relationships defined in the markdown.
    * `source`: The `id` of the entity where the relationship originates.
    * `target`: The `id` of the entity the relationship points to.
    * `label`: The relationship type defined using `- Relationship: relationship_type`.


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