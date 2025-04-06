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
- MCP client requires Crystal lang and shards.

## Installation

*Wait we're not using named pipes anymore, it's STDIN, also the MCP client boots the MCP server which loads up the CYBERON data access module. So there's also no systemd configuration because the server is not persistent. This is a note to myself to go undo that configuration and update the instructions... later.*

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

(Needs update to reflect the Crystal clients)

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

## Input Formatting

### Markdown Format

The system processes markdown-formatted ontology files adhering to the following structure, allowing for hierarchical categorization using heading levels H1-H6.

```Markdown
# H1 Category Name

## H2 Sub-Category Name

### H3 Sub-Sub-Category Name

Headings (H1-H6) define categories and sub-categories.  
Entities belong to the most specific (deepest) category defined before them.

- Entity: EntityName1  
  Description: A brief description of this entity.  
  Type: EntityType  
  Attributes:  
    - Attribute: AttributeName1  
      Value: Some Value  
    - Attribute: AttributeName2 [url:/path/to/resource]  
      Value: Another Value  
  Relationships:  
    - Relationship: relationship_type_1  
      Target: TargetEntityName1  
    - Relationship: relationship_type_2  
      Target: TargetEntityName2

  > This defines a new entity.  
  > Description is optional and provides a human-readable explanation.  
  > Type is optional and can classify the entity (e.g., Species, Organ, Concept, Person, Category).  
  > Attributes are optional and define specific properties of the entity.  
  > Relationships are optional and specify links to other entities.

- Entity: EntityName2  
  Description: Another entity.  
  Type: AnotherType  

  > This entity has no explicit attributes or relationships.

# Another H1 Category

## Another H2 Sub-Category

- Entity: TargetEntityName1  
  Description: An entity in the second H2 category.  
  Type: TargetType

```

### Key Syntax Points

#### Categories (Headings):

-   Use H1 (`#`) through H6 (`######`) to define categories and sub-categories.
-   The heading level determines the depth in the hierarchy.
-   Entities belong to the category defined by the most recent heading of any level.

#### Entities:

-   Define entities using `- Entity: EntityName`.

##### Entity Properties:

-   Define properties directly under `- Entity:`:
    -   `Description:` Text (Optional description)
    -   `Type:` Text (Optional type classification)

#### Attributes Block:

-   Start with `Attributes:`.
-   List attributes using `- Attribute: AttributeName`.
    -   Optionally include `[url:/path/...]` at the end of the `- Attribute:` line for a URL.
-   Provide the value on the next line using `Value: AttributeValue`.
-   **Important:** Each `- Attribute:` must be immediately followed by `Value:`.

#### Relationships Block:

-   Start with `Relationships:`.
-   Define relationships using `- Relationship: relationship_type`.
-   Specify the target on the next line using `Target: TargetEntityName`. Inline comments (`# ...`) after the target name are stripped.
-   **Important:** Each `- Relationship:` must be immediately followed by `Target:`.

#### Order Matters:

-   `Value:` must follow `- Attribute:`.
-   `Target:` must follow `- Relationship:`.
-   Attributes must be under `Attributes:`.
-   Relationships must be under `Relationships:`.
-   An entity's category is determined by the last heading encountered before it.

---

## Data Output: Knowledge Graph

The system processes the markdown into a knowledge graph JSON format with `nodes` and `edges`.

### Node Structure

All nodes (representing entities *and* categories) share a standard structure:

```json
{
  "id": "unique_node_id", // Lowercase, underscore-separated ID from name/heading
  "label": "Original Name or Heading", // The original text
  "type": "EntityType or Category", // Type defined in Markdown, or "Category" for headings
  "description": "Optional description text.", // From Description: field, if present
  "attributes": { // Node-specific attributes nested in a dictionary
    "attribute_id_1": {
        "value": "Some Value",
        "url": null // or "/path/to/resource" if provided
     },
    "attribute_id_2": {
        "value": "Another Value",
        "url": "/path/to/resource"
     }
     // ... other attributes
  }
}
```

-   `id`: Generated ID (e.g., `entity_name_1`, `h1_category_name`, `h2_sub_category_name`).
-   `label`: Original name from `- Entity:` or heading text.
-   `type`: From `Type:` field, or automatically set to `Category`.
-   `description`: From `Description:` field.
-   `attributes`: A dictionary containing key-value pairs for attributes defined in the `Attributes:` block.
    -   The key is the generated ID of the attribute name (e.g., `attribute_name_1`).
    -   The value is an object containing `value` and optional `url`.

### Edge Structure

Edges represent relationships between nodes:

1.  **Entity-to-Entity:** Defined in the `Relationships:` block.
    ```json
    {
      "source": "entity_id_1",
      "target": "entity_id_2",
      "label": "relationship_type"
    }
    ```
2.  **Category-to-Category (Hierarchy):** Automatically generated based on heading levels.
    ```json
    {
      "source": "parent_category_id", // e.g., ID from H1 heading
      "target": "child_category_id", // e.g., ID from H2 heading under the H1
      "label": "has_subcategory" // Standard label for hierarchy
    }
    ```
3.  **Entity-to-Category (Membership):** Automatically generated link from an entity to its most specific category.
    ```json
    {
      "source": "entity_id",
      "target": "most_specific_category_id", // ID of the H1/H2/H3... node it belongs to
      "label": "belongs_to_category" // Standard label for membership
    }
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