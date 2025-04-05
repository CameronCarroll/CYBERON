import re
import json
from typing import Dict, List, Set, Tuple, Any, Optional

def parse_markdown_ontology(markdown_text: str) -> Dict:
    """
    Parse a markdown-formatted ontology document into a structured dictionary
    
    Args:
        markdown_text: Markdown text content
        
    Returns:
        Dictionary representation of the structured ontology
    """
    if not markdown_text.strip():
        return {}

    lines = markdown_text.strip().split('\n')
    structured_ontology = {}
    current_section = None
    current_subsection = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Process H1 (main section)
        if line.startswith('# '):
            section_title = line[2:].strip()
            section_id = make_id(section_title)
            structured_ontology[section_id] = {
                "title": section_title,
                "subsections": {}
            }
            current_section = section_id
            current_subsection = None
        
        # Process H2 (subsection)
        elif line.startswith('## ') and current_section:
            subsection_title = line[3:].strip()
            structured_ontology[current_section]["subsections"][subsection_title] = []
            current_subsection = subsection_title
        
        # Process list items (Entities)
        elif line.startswith('- Entity: ') and current_section and current_subsection:
            entity_name = line[9:].strip()
            entity_data = {"name": entity_name, "description": "", "type": ""}
            
            # Consume subsequent lines for description, type, attributes, and relationships
            i = lines.index(line) + 1
            while i < len(lines) and not lines[i].startswith(('#', '##', '-')):
                sub_line = lines[i].strip()
                if sub_line.startswith("Description:"):
                    entity_data["description"] = sub_line[12:].strip()
                elif sub_line.startswith("Type:"):
                    entity_data["type"] = sub_line[6:].strip()
                elif sub_line.startswith("Attributes:"):
                    entity_data["attributes"] = []
                    i += 1
                    while i < len(lines) and lines[i].strip().startswith("- Attribute:"):
                        attr_line = lines[i].strip()
                        attr_name = attr_line[11:].split("Value:")[0].strip()
                        attr_value = attr_line[11:].split("Value:")[1].strip()
                        entity_data["attributes"].append({"name": attr_name, "value": attr_value})
                        i += 1
                    i -= 1 # adjust i back since the outer loop will increment it
                elif sub_line.startswith("Relationships:"):
                    entity_data["relationships"] = []
                    i += 1
                    while i < len(lines) and lines[i].strip().startswith("- Relationship:"):
                        rel_line = lines[i].strip()
                        rel_type = rel_line[14:].split("Target:")[0].strip()
                        rel_target = rel_line[14:].split("Target:")[1].strip()
                        entity_data["relationships"].append({"type": rel_type, "target": rel_target})
                        i += 1
                    i -= 1  # adjust i back since the outer loop will increment it
                i += 1
            structured_ontology[current_section]["subsections"][current_subsection].append(entity_data)
    return structured_ontology

def make_id(text: str) -> str:
    """
    Convert a title or name to a valid ID format
    
    Args:
        text: The input text to convert
        
    Returns:
        A lowercase, underscore-separated ID
    """
    return re.sub(r'[^a-z0-9_]', '_', text.lower()).strip('_')

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

def convert_to_knowledge_graph(structured_ontology: Dict) -> Dict:
    """
    Convert the structured ontology into a knowledge graph format
    
    Args:
        structured_ontology: Dictionary with the structured ontology
        
    Returns:
        Knowledge graph as a dictionary with "nodes" and "edges" lists
    """
    people, concepts, domains = extract_entities(structured_ontology)
    
    nodes = []
    edges = []
    
    for section_id, section_data in structured_ontology.items():
        section_title = section_data["title"]
        nodes.append({
            "id": section_id,
            "label": section_title,
            "type": "category"
        })
        
        for subsection_name, items in section_data["subsections"].items():
            subsection_id = make_id(subsection_name)
            nodes.append({
                "id": subsection_id,
                "label": subsection_name,
                "type": "category"
            })
            edges.append({
                "source": section_id,
                "target": subsection_id,
                "label": "contains"
            })
            
            for item in items:
                item_name = item["name"]
                item_id = make_id(item_name)
                item_type = item["type"] # Get the type directly from the item
                
                # Add the node only if it doesn't exist
                if not any(node["id"] == item_id for node in nodes):
                    node_data = {
                        "id": item_id,
                        "label": item_name,
                        "type": item_type,
                    }
                    if "attributes" in item:
                        node_data["attributes"] = item["attributes"]
                    nodes.append(node_data)
                
                edges.append({
                    "source": subsection_id,
                    "target": item_id,
                    "label": "includes"
                })
                
                # Add relationships
                if "relationships" in item:
                    for rel in item["relationships"]:
                        target_id = make_id(rel["target"])
                        edges.append({
                            "source": item_id,
                            "target": target_id,
                            "label": rel["type"]
                        })
    
    return {
        "nodes": nodes,
        "edges": edges
    }

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