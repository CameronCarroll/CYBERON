import re
import json
from typing import Dict, List, Set, Tuple, Any, Optional

def make_id(text: str) -> str:
    """
    Convert a title or name to a valid ID format (lowercase, underscore-separated).
    """
    # Replace sequences of non-alphanumeric characters with a single underscore
    s = re.sub(r'[^a-z0-9]+', '_', text.lower())
    # Remove leading/trailing underscores
    return s.strip('_')

def parse_markdown_ontology(markdown_text: str) -> Dict[str, Any]:
    """
    Parse a markdown-formatted ontology document into a structured dictionary.
    Handles multi-line attributes/relationships and attribute URLs.

    Args:
        markdown_text: Markdown text content.

    Returns:
        Dictionary representing the structured ontology, organized by section.
        Example: {'biology': {'title': 'Biology', 'entities': [...]}}
    """
    structured_ontology: Dict[str, Any] = {}
    lines = [line for line in markdown_text.strip().split('\n') if line.strip() and not line.strip().startswith('##')] # Ignore empty lines and H2

    current_section_id: Optional[str] = None
    current_entity: Optional[Dict[str, Any]] = None
    parsing_state: Optional[str] = None # 'attributes' or 'relationships'
    last_attribute_line: Optional[str] = None
    last_relationship_line: Optional[str] = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Section Header
        if line.startswith('# '):
            section_title = line[2:].strip()
            section_id = make_id(section_title)
            if section_id not in structured_ontology:
                structured_ontology[section_id] = {"title": section_title, "entities": []}
            current_section_id = section_id
            current_entity = None # Reset entity context when section changes
            parsing_state = None
            i += 1
            continue

        # Start of Entity
        if line.startswith('- Entity:'):
            if current_section_id is None:
                # Or raise an error, or log a warning
                print(f"Warning: Entity definition found before any section header: {line}")
                i += 1
                continue
            entity_name = line[len('- Entity:'):].strip()
            current_entity = {
                "name": entity_name,
                "description": None,
                "type": None,
                "attributes": [],
                "relationships": []
            }
            structured_ontology[current_section_id]["entities"].append(current_entity)
            parsing_state = None # Reset state for new entity
            i += 1
            continue

        # Inside an Entity definition
        if current_entity is not None:
            # Description
            if line.startswith('Description:'):
                current_entity['description'] = line[len('Description:'):].strip()
                parsing_state = None
            # Type
            elif line.startswith('Type:'):
                current_entity['type'] = line[len('Type:'):].strip()
                parsing_state = None
            # Attributes Header
            elif line.startswith('Attributes:'):
                parsing_state = 'attributes'
            # Relationships Header
            elif line.startswith('Relationships:'):
                parsing_state = 'relationships'

            # Parsing Attributes Block
            elif parsing_state == 'attributes':
                if line.startswith('- Attribute:'):
                    # Store this line and expect Value: on the next line
                    last_attribute_line = line
                elif line.startswith('Value:') and last_attribute_line is not None:
                    attr_value = line[len('Value:'):].strip()
                    # Process the stored attribute line
                    attr_line_content = last_attribute_line[len('- Attribute:'):].strip()
                    url_match = re.search(r'^(.*)\[url:(.*)\]$', attr_line_content)
                    attr_name: str
                    attr_url: Optional[str] = None
                    if url_match:
                        attr_name = url_match.group(1).strip()
                        attr_url = url_match.group(2).strip()
                    else:
                        attr_name = attr_line_content.strip()

                    current_entity['attributes'].append({
                        "name": attr_name,
                        "value": attr_value,
                        "url": attr_url
                    })
                    last_attribute_line = None # Reset after processing
                else:
                    # Line doesn't match expected attribute structure, reset state? Or log warning?
                    # Assuming here it might be a malformed entry or end of block
                    # parsing_state = None # Or handle more gracefully if needed
                    pass # Keep parsing_state='attributes' until Relationships: or new entity/section
            
            # Parsing Relationships Block
            elif parsing_state == 'relationships':
                if line.startswith('- Relationship:'):
                    # Store this line and expect Target: on the next line
                    last_relationship_line = line
                elif line.startswith('Target:') and last_relationship_line is not None:
                    # Strip potential inline comments
                    target_name = line[len('Target:'):].split('#')[0].strip()
                    # Process the stored relationship line
                    rel_type = last_relationship_line[len('- Relationship:'):].strip()

                    current_entity['relationships'].append({
                        "type": rel_type,
                        "target": target_name
                    })
                    last_relationship_line = None # Reset after processing
                else:
                     # Line doesn't match expected relationship structure
                     # parsing_state = None
                     pass

            # Line doesn't match any known entity property/block start
            else:
                 # Could be whitespace within entity block, or malformed. Ignored for now.
                 pass

        i += 1 # Move to the next line

    return structured_ontology

def extract_entities(structured_ontology: Dict) -> Tuple[Set[str], Set[str], Dict[str, List[Dict]]]:
    """
    Extract people, concepts, and domains from the structured ontology
    
    Args:
        structured_ontology: Dictionary with the structured ontology
        
    Returns:
        Tuple of (people, concepts, domains) where:
          - people is a set of person names
          - concepts is a set of concept names
          - domains is a dictionary mapping domain names to lists of items
    """
    people = set()
    concepts = set()
    domains = {}
    
    for section_id, section_data in structured_ontology.items():
        section_title = section_data["title"]
        for subsection_name, items in section_data["subsections"].items():
            domain_name = f"{section_title} - {subsection_name}"
            domains[domain_name] = items
            for item in items:
                if item["type"] == "Person":
                    people.add(item["name"])
                else:
                    concepts.add(item["name"])
    
    return people, concepts, domains

def convert_to_knowledge_graph(structured_ontology: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Convert the structured ontology into the specified knowledge graph JSON format.

    Args:
        structured_ontology: Dictionary generated by parse_markdown_ontology.

    Returns:
        Knowledge graph as a dictionary with "nodes" and "edges" lists.
    """
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    node_ids: Set[str] = set() # Keep track of added nodes to avoid duplicates

    for section_id, section_data in structured_ontology.items():
        # Add section node if not already added (though unlikely with this structure)
        if section_id not in node_ids:
            nodes.append({
                "id": section_id,
                "label": section_data['title'],
                "type": "category" # As per original example output
            })
            node_ids.add(section_id)

        # Process entities within the section
        for entity in section_data['entities']:
            entity_id = make_id(entity['name'])

            # Create or update node for the entity
            # Check if node exists primarily for target entities that might be defined later
            node_entry = next((node for node in nodes if node["id"] == entity_id), None)
            if node_entry is None:
                 node_entry = {"id": entity_id}
                 nodes.append(node_entry)
                 node_ids.add(entity_id)

            # Populate node details (overwrite if target was defined before source)
            node_entry["label"] = entity['name']
            if entity['type']:
                node_entry["type"] = entity['type']
            if entity['description']:
                node_entry["description"] = entity['description']

            # Add attributes as direct key-value pairs
            for attribute in entity['attributes']:
                attr_id = make_id(attribute['name'])
                node_entry[attr_id] = attribute['value']
                if attribute['url']:
                    node_entry[f"{attr_id}_url"] = attribute['url']

            # Create edges for relationships
            for relationship in entity['relationships']:
                target_id = make_id(relationship['target'])
                # Ensure target node exists (create a basic one if not)
                if target_id not in node_ids:
                    # Find target entity details if defined elsewhere, otherwise create placeholder
                    target_label = relationship['target'] # Default label
                    target_type = "Unknown" # Default type
                    # Look ahead (or back) for target definition (optional enhancement)
                    # For simplicity now, just create placeholder if completely missing
                    nodes.append({"id": target_id, "label": target_label, "type": target_type})
                    node_ids.add(target_id)


                edges.append({
                    "source": entity_id,
                    "target": target_id,
                    "label": relationship['type']
                })

    return {"nodes": nodes, "edges": edges}

def extract_markdown_to_json(input_file: str, output_file: str) -> None:
    """
    Process a markdown ontology file and save as structured JSON
    
    Args:
        input_file: Path to the input markdown file
        output_file: Path to save the output JSON file
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    structured_ontology = parse_markdown_ontology(markdown_text)
    knowledge_graph = convert_to_knowledge_graph(structured_ontology)
    
    result = {
        "structured_ontology": structured_ontology,
        "knowledge_graph": knowledge_graph
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"Ontology processed and saved to {output_file}")
    print(f"Found {len(knowledge_graph['nodes'])} nodes and {len(knowledge_graph['edges'])} relationships")

def analyze_ontology_structure(structured_ontology: Dict) -> Dict:
    """
    Analyze the structure of the ontology for insights
    
    Args:
        structured_ontology: The structured ontology dictionary
        
    Returns:
        Dictionary with analysis results
    """
    analysis = {
        "section_count": len(structured_ontology),
        "total_subsections": 0,
        "total_concepts": 0,
        "total_entities": 0, # Add total entities
        "section_sizes": {},
        "largest_sections": [],
        "most_connected_concepts": []
    }
    
    # Count subsections and concepts
    for section_id, section_data in structured_ontology.items():
        subsection_count = len(section_data["subsections"])
        analysis["total_subsections"] += subsection_count
        
        entity_count = 0
        for _, items in section_data["subsections"].items():
            entity_count += len(items)
        
        analysis["total_entities"] += entity_count # Update total entities
        analysis["section_sizes"][section_id] = {
            "title": section_data["title"],
            "subsections": subsection_count,
            "entities": entity_count # track entities per section
        }
    
    # Find the largest sections
    largest_sections = sorted(
        [(k, v["subsections"], v["entities"], v["title"])  # Use "entities"
         for k, v in analysis["section_sizes"].items()],
        key=lambda x: (x[1], x[2]),
        reverse=True
    )[:3]
    
    analysis["largest_sections"] = [
        {"number": i+1, "id": num, "title": title, "subsections": subs, "entities": entities}
        for i, (num, subs, entities, title) in enumerate(largest_sections)
    ]
    
    return analysis