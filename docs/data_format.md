# Cyberon Data Formats

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

-   Use H1 (`#`) through H6 (`######`) to define categories and sub-categories
-   The heading level determines the depth in the hierarchy
-   Entities belong to the category defined by the most recent heading of any level

#### Entities:

-   Define entities using `- Entity: EntityName`

##### Entity Properties:

-   Define properties directly under `- Entity:`:
    -   `Description:` Text (Optional description)
    -   `Type:` Text (Optional type classification)

#### Attributes Block:

-   Start with `Attributes:`.
-   List attributes using `- Attribute: AttributeName`
    -   Optionally include `[url:/path/...]` at the end of the `- Attribute:` line for a URL.
-   Provide the value on the next line using `Value: AttributeValue`
-   **Important:** Each `- Attribute:` must be immediately followed by `Value:`

#### Relationships Block:

-   Start with `Relationships:`
-   Define relationships using `- Relationship: relationship_type`
-   Specify the target on the next line using `Target: TargetEntityName`. Inline comments (`# ...`) after the target name are stripped.
-   **Important:** Each `- Relationship:` must be immediately followed by `Target:`

#### Order Matters:

-   `Value:` must follow `- Attribute:`
-   `Target:` must follow `- Relationship:`
-   Attributes must be under `Attributes:`
-   Relationships must be under `Relationships:`
-   An entity's category is determined by the last heading encountered before it

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
