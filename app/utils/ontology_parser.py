import re
import json
from typing import Dict, List, Set, Tuple, Any, Optional

# --- Utility Functions ---

def make_id(text: str) -> str:
    """
    Convert a title or name to a valid ID format (lowercase, underscore-separated).
    Handles potential multiple non-alphanumeric chars together.
    """
    # Replace sequences of non-alphanumeric characters with a single underscore
    s = re.sub(r'[^a-z0-9]+', '_', text.lower())
    # Remove leading/trailing underscores that might result
    return s.strip('_')

# --- Parsing Function ---

def parse_markdown_ontology(markdown_text: str) -> List[Dict[str, Any]]:
    """
    Parses a markdown-formatted ontology document with hierarchical headings (H1-H6)
    into a tree structure representing categories and their entities.

    Args:
        markdown_text: Markdown text content.

    Returns:
        A list representing the root categories (H1s) of the ontology tree.
        Each node in the tree (category or entity) contains its relevant data.
        Category Node Structure:
            {
                'id': str,
                'label': str,
                'level': int,
                'type': 'Category',
                'description': Optional[str], # Placeholder for potential future category descriptions
                'children': List[Dict], # Child Category nodes
                'entities': List[Dict] # Entities belonging directly to this category
            }
        Entity Node Structure (within category['entities']):
            {
                'name': str,
                'description': Optional[str],
                'type': Optional[str],
                'attributes': List[Dict], # Raw parsed attributes
                'relationships': List[Dict] # Raw parsed relationships
            }
    """
    ontology_tree: List[Dict[str, Any]] = [] # Holds the top-level (H1) categories
    # Stack stores tuples: (level, category_node_reference)
    parent_stack: List[Tuple[int, Dict[str, Any]]] = []
    current_entity: Optional[Dict[str, Any]] = None
    parsing_state: Optional[str] = None # 'attributes' or 'relationships'
    last_attribute_line: Optional[str] = None
    last_relationship_line: Optional[str] = None

    lines = markdown_text.strip().split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1 # Increment early for easier continue/processing logic

        if not line: # Skip empty lines
            continue

        # --- 1. Handle Headings (Categories) ---
        heading_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            category_id = make_id(title)

            category_node: Dict[str, Any] = {
                "id": category_id,
                "label": title,
                "level": level,
                "type": "Category",
                "description": None, # Categories don't have descriptions in the spec yet
                "children": [],
                "entities": []
            }

            # Adjust parent stack based on level
            while parent_stack and parent_stack[-1][0] >= level:
                parent_stack.pop()

            # Add to parent or root list
            if parent_stack:
                parent_category = parent_stack[-1][1]
                parent_category["children"].append(category_node)
            else:
                ontology_tree.append(category_node)

            # Push current category onto stack
            parent_stack.append((level, category_node))

            current_entity = None # Reset entity context when category changes
            parsing_state = None
            continue # Move to next line

        # --- 2. Handle Entity Definitions ---
        if line.startswith('- Entity:'):
            if not parent_stack:
                 # Error or warning: Entity defined outside any category
                 print(f"Warning: Entity definition found before any category heading: {line}")
                 # Decide handling: skip, add to a default root, etc. Here we skip.
                 current_entity = None
                 continue

            entity_name = line[len('- Entity:'):].strip()
            current_entity = {
                "name": entity_name,
                "description": None,
                "type": None, # Default type if not specified
                "attributes": [],
                "relationships": []
            }
            # Add the new entity to the *current* deepest category
            current_category_node = parent_stack[-1][1]
            current_category_node["entities"].append(current_entity)
            parsing_state = None # Reset state for new entity
            continue

        # --- 3. Handle Properties within the Current Entity ---
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
                last_attribute_line = None # Reset just in case
            # Relationships Header
            elif line.startswith('Relationships:'):
                parsing_state = 'relationships'
                last_relationship_line = None # Reset just in case

            # Parsing Attributes Block
            elif parsing_state == 'attributes':
                if line.startswith('- Attribute:'):
                    # Store this line, expect Value: next
                    last_attribute_line = line
                elif line.startswith('Value:') and last_attribute_line is not None:
                    # --- Apply Fix Here ---
                    # Original line:
                    # attr_value = line[len('Value:'):].strip()
                    # Fixed line: Split at '#' to remove inline comments and strip whitespace
                    attr_value_raw = line[len('Value:'):]
                    attr_value = attr_value_raw.split('#', 1)[0].strip() # Split only once
                    # --- End Fix ---

                    # Process the stored attribute line
                    attr_line_content = last_attribute_line[len('- Attribute:'):].strip()
                    url_match = re.search(r'^(.*)\[url:(.*)\]$', attr_line_content)
                    attr_name: str
                    attr_url: Optional[str] = None
                    if url_match:
                        attr_name = url_match.group(1).strip()
                        attr_url = url_match.group(2).strip()
                    else:
                        attr_name = attr_line_content

                    current_entity['attributes'].append({
                        "name": attr_name,
                        "value": attr_value, # Use the cleaned value
                        "url": attr_url
                    })
                    last_attribute_line = None # Reset after successful pair processing
                # Ignore lines not matching the pair structure within the attributes block
                # else: pass

            # Parsing Relationships Block
            elif parsing_state == 'relationships':
                if line.startswith('- Relationship:'):
                    # Store this line, expect Target: next
                    last_relationship_line = line
                elif line.startswith('Target:') and last_relationship_line is not None:
                    # Strip potential inline comments
                    target_name = line[len('Target:'):].split('#')[0].strip()
                    # Process the stored relationship line
                    rel_type = last_relationship_line[len('- Relationship:'):].strip()

                    current_entity['relationships'].append({
                        "type": rel_type,
                        "target": target_name # Store target name, resolve to ID later
                    })
                    last_relationship_line = None # Reset after successful pair processing
                # Ignore lines not matching the pair structure within the relationships block
                # else: pass
            # Ignore other lines within an entity scope
            # else: pass
        # Ignore lines not matching any known pattern if not inside an entity
        # else: pass

    return ontology_tree


# --- Conversion Function ---

def convert_to_knowledge_graph(ontology_tree: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Convert the hierarchical ontology tree into the specified knowledge graph JSON format,
    including category nodes, hierarchy edges, entity-category edges, and standardized
    node structure with nested attributes.

    Args:
        ontology_tree: Hierarchical structure generated by parse_markdown_ontology.

    Returns:
        Knowledge graph as a dictionary with "nodes" and "edges" lists.
    """
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    node_ids: Set[str] = set() # Keep track of added node IDs to avoid duplicates

    # Recursive function to process categories and entities
    def process_node(item: Dict[str, Any], parent_category_id: Optional[str]):
        nonlocal nodes, edges, node_ids # Allow modification of outer scope variables

        item_id = "" # Initialize item_id

        # --- A. Process Category Node ---
        if item.get('type') == 'Category':
            item_id = item['id']
            if item_id not in node_ids:
                category_node = {
                    "id": item_id,
                    "label": item['label'],
                    "type": "Category",
                    "description": item.get('description'), # Use .get for safety
                    "attributes": {} # Categories don't have markdown attributes in this spec
                }
                nodes.append(category_node)
                node_ids.add(item_id)

            # Create hierarchy edge if it has a parent
            if parent_category_id:
                edges.append({
                    "source": parent_category_id,
                    "target": item_id,
                    "label": "has_subcategory"
                })

            # Recursively process child categories
            for child_category in item.get('children', []):
                process_node(child_category, item_id) # Pass current category ID as parent

            # Recursively process entities within this category
            for entity_data in item.get('entities', []):
                process_node(entity_data, item_id) # Pass current category ID as parent

        # --- B. Process Entity Node ---
        else: # It's an entity dictionary
            entity_name = item['name']
            item_id = make_id(entity_name)

            # Create attributes dictionary in the required nested format
            attributes_dict = {}
            for attr in item.get('attributes', []):
                attr_id = make_id(attr['name'])
                attributes_dict[attr_id] = {
                    "value": attr['value'],
                    "url": attr.get('url') # Use .get for optional URL
                }

            # Create the entity node
            entity_node = {
                "id": item_id,
                "label": entity_name,
                 # Use 'Unknown' or a default if type is None/empty
                "type": item.get('type') or "UnknownEntity",
                "description": item.get('description'),
                "attributes": attributes_dict
            }

            # Add or update node (in case it was added as a target placeholder earlier)
            existing_node = next((n for n in nodes if n["id"] == item_id), None)
            if existing_node:
                 # Update existing placeholder node with full details
                 existing_node.update(entity_node)
            elif item_id not in node_ids:
                 nodes.append(entity_node)
                 node_ids.add(item_id)
            # else: Node already fully defined, ignore (should ideally not happen often with tree traversal)

            # Create entity-to-category edge
            if parent_category_id:
                edges.append({
                    "source": item_id,
                    "target": parent_category_id,
                    "label": "belongs_to_category"
                })
            else:
                # This case should be handled/warned in parsing, but defensively:
                print(f"Warning: Entity '{entity_name}' (ID: {item_id}) has no parent category.")


            # Create entity-to-entity relationship edges
            for relationship in item.get('relationships', []):
                target_name = relationship['target']
                target_id = make_id(target_name)

                # Ensure target node exists (create basic placeholder if not)
                if target_id not in node_ids:
                    # Basic placeholder - might be updated later if target is defined
                    nodes.append({
                        "id": target_id,
                        "label": target_name, # Use original name for label
                        "type": "Unknown", # Mark as unknown type initially
                        "description": None,
                        "attributes": {}
                    })
                    node_ids.add(target_id)

                # Add the relationship edge
                edges.append({
                    "source": item_id, # Source is the current entity
                    "target": target_id,
                    "label": relationship['type']
                })

    # --- Initial call to start processing from root categories ---
    for root_category in ontology_tree:
        process_node(root_category, parent_category_id=None)

    return {"nodes": nodes, "edges": edges}


# --- Helper functions (extract_entities, analyze_ontology_structure) ---
# These might need adjustments based on the NEW structure returned by parse_markdown_ontology
# OR they might operate on the FINAL knowledge graph output.
# Let's update `analyze_ontology_structure` to work with the new parser output (ontology_tree)
# and `extract_entities` to work from the final KG nodes.

def extract_entities(knowledge_graph: Dict[str, List[Dict[str, Any]]]) -> Tuple[Set[str], Set[str], Dict[str, List[Dict]]]:
    """
    Extracts people, concepts (non-Person, non-Category entities), and categories
    from the generated knowledge graph nodes.

    Args:
        knowledge_graph: Dictionary with "nodes" and "edges".

    Returns:
        Tuple of (people, concepts, categories) where:
          - people is a set of person labels (if type is 'Person')
          - concepts is a set of labels for other non-category entities
          - categories is a dictionary mapping category labels to category node info
            (or just a set of category labels if details aren't needed).
    """
    people = set()
    concepts = set()
    categories = {} # Store label -> node details (or just labels if preferred)

    for node in knowledge_graph.get("nodes", []):
        node_type = node.get("type")
        node_label = node.get("label", "") # Use label for sets

        if node_type == "Person":
            people.add(node_label)
        elif node_type == "Category":
            categories[node_label] = node # Store full node or just node_label
        elif node_type and node_type not in ["Unknown", "UnknownEntity"]: # Assume other defined types are concepts
            concepts.add(node_label)
        # Decide how to handle "Unknown" or "UnknownEntity" types if needed

    return people, concepts, categories


def analyze_ontology_structure(ontology_tree: List[Dict[str, Any]]) -> Dict:
    """
    Analyze the hierarchical structure of the ontology tree for insights.

    Args:
        ontology_tree: The hierarchical list/dict structure from parse_markdown_ontology.

    Returns:
        Dictionary with analysis results (counts, sizes, etc.).
    """
    analysis = {
        "root_category_count": len(ontology_tree),
        "total_categories": 0,
        "total_entities": 0,
        "max_depth": 0,
        "category_entity_counts": {}, # category_id -> {'label': ..., 'entities': count, 'subcategories': count}
        # Add more metrics as needed
    }

    def traverse_analyze(category_node: Dict[str, Any], current_depth: int):
        nonlocal analysis
        analysis["total_categories"] += 1
        analysis["max_depth"] = max(analysis["max_depth"], current_depth)

        cat_id = category_node['id']
        entity_count = len(category_node.get('entities', []))
        subcategory_count = len(category_node.get('children', []))
        analysis["total_entities"] += entity_count
        analysis["category_entity_counts"][cat_id] = {
            "label": category_node['label'],
            "level": category_node['level'],
            "entities": entity_count,
            "direct_subcategories": subcategory_count
        }

        for entity in category_node.get('entities', []):
            # Could analyze entity types here if needed
            pass

        for subcategory in category_node.get('children', []):
            traverse_analyze(subcategory, current_depth + 1)

    # Start traversal from root categories
    for root_category in ontology_tree:
        traverse_analyze(root_category, 1) # Start depth at 1 for H1

    # Example: Find largest categories by entity count (can be adapted)
    # analysis["largest_categories_by_entities"] = sorted(
    #     [
    #         {"id": k, "label": v["label"], "entities": v["entities"]}
    #         for k, v in analysis["category_entity_counts"].items()
    #     ],
    #     key=lambda x: x["entities"],
    #     reverse=True
    # )[:5] # Top 5

    return analysis


# --- Main Processing Function ---

def extract_markdown_to_json(input_file: str, output_file: str) -> None:
    """
    Process a hierarchical markdown ontology file and save the resulting
    knowledge graph as JSON. Includes intermediate structure and analysis.

    Args:
        input_file: Path to the input markdown file.
        output_file: Path to save the output JSON file.
    """
    print(f"Processing Markdown file: {input_file}")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_file}")
        return
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    # Phase 1: Parse Markdown into hierarchical tree
    print("Parsing Markdown into hierarchical structure...")
    ontology_tree = parse_markdown_ontology(markdown_text)
    if not ontology_tree:
        print("Warning: No categories found or parsed from the Markdown.")
        # Decide if processing should stop or continue with empty data

    # Phase 2: Convert tree to Knowledge Graph format
    print("Converting hierarchical structure to Knowledge Graph...")
    knowledge_graph = convert_to_knowledge_graph(ontology_tree)

    # Phase 3: Analyze the structure (optional but useful)
    print("Analyzing ontology structure...")
    analysis_results = analyze_ontology_structure(ontology_tree)
    # Can also analyze the final KG if preferred:
    # people, concepts, categories = extract_entities(knowledge_graph)

    # Combine results for output
    result = {
        # Include the intermediate tree for debugging/verification if useful
        # "ontology_tree": ontology_tree,
        "knowledge_graph": knowledge_graph,
        "analysis": analysis_results
        # "extracted_elements": { # Example if using extract_entities
        #     "people": list(people),
        #     "concepts": list(concepts),
        #     "categories": list(categories.keys())
        # }
    }

    # Save the final JSON output
    print(f"Saving results to {output_file}...")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False) # Use ensure_ascii=False for wider char support
        print("-" * 20)
        print(f"Ontology processed successfully.")
        print(f"Knowledge Graph: {len(knowledge_graph['nodes'])} nodes, {len(knowledge_graph['edges'])} edges.")
        print(f"Analysis Summary:")
        print(f"  - Root Categories: {analysis_results['root_category_count']}")
        print(f"  - Total Categories: {analysis_results['total_categories']}")
        print(f"  - Total Entities: {analysis_results['total_entities']}")
        print(f"  - Max Category Depth: {analysis_results['max_depth']}")
        print("-" * 20)

    except Exception as e:
        print(f"Error writing output file: {e}")