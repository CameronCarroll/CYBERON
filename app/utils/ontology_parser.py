import re
import json
from typing import Dict, List, Set, Tuple, Any, Optional
import markdown
from bs4 import BeautifulSoup

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
    
    # Process the markdown lines directly without BeautifulSoup
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
            
        # Process H3 (specialized subsection)
        elif line.startswith('### ') and current_section:
            subsection_title = line[4:].strip()
            structured_ontology[current_section]["subsections"][subsection_title] = []
            current_subsection = subsection_title
            
        # Process list items
        elif line.startswith('- ') and current_section and current_subsection:
            # Extract the item content without the leading '-'
            item_content = line[2:].strip()
            
            # Process URL notation, e.g., "Entity Name [url:/path/to/resource.html]: Description"
            url_pattern = re.compile(r'(.*?)\s*\[url:(.*?)\](.*)')
            url_match = url_pattern.match(item_content)
            
            # Check if there's a URL
            if url_match:
                name = url_match.group(1).strip()
                external_url = url_match.group(2).strip()
                rest = url_match.group(3).strip()
                
                # Check if there's a description after the colon
                if rest.startswith(':'):
                    description = rest[1:].strip()
                    structured_ontology[current_section]["subsections"][current_subsection].append({
                        "name": name,
                        "description": description,
                        "external_url": external_url
                    })
                else:
                    # Item has a URL but no description
                    structured_ontology[current_section]["subsections"][current_subsection].append({
                        "name": name,
                        "description": "",
                        "external_url": external_url
                    })
            else:
                # No URL, standard format "Entity Name: Description"
                parts = item_content.split(':', 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    description = parts[1].strip()
                    structured_ontology[current_section]["subsections"][current_subsection].append({
                        "name": name,
                        "description": description
                    })
                else:
                    # Item without a description
                    structured_ontology[current_section]["subsections"][current_subsection].append({
                        "name": item_content,
                        "description": ""
                    })
    
    # Verify we have at least one top-level section, otherwise the markdown was malformed
    if not structured_ontology:
        raise ValueError("Malformed markdown: No top-level headings (H1) found")
    
    return structured_ontology

def make_id(text: str) -> str:
    """
    Convert a title or name to a valid ID format
    
    Args:
        text: The input text to convert
        
    Returns:
        A lowercase, underscore-separated ID
    """
    # Convert to lowercase and replace spaces/non-alphanumeric chars with underscores
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
    
    # Process each section
    for section_id, section_data in structured_ontology.items():
        section_title = section_data["title"]
        
        # Process each subsection
        for subsection_name, items in section_data["subsections"].items():
            # Create a domain entry for this subsection
            domain_name = f"{section_title} - {subsection_name}"
            domains[domain_name] = items
            
            # Categorize items as people or concepts
            if "Key Figures" in subsection_name or "People" in subsection_name or "Person" in subsection_name:
                # Items in these subsections are assumed to be people
                for item in items:
                    people.add(item["name"])
            else:
                # All other items are assumed to be concepts
                for item in items:
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
    people, concepts, domains_items = extract_entities(structured_ontology)
    
    nodes = []
    edges = []
    
    # Add section nodes
    for section_id, section_data in structured_ontology.items():
        section_title = section_data["title"]
        
        nodes.append({
            "id": section_id,
            "label": section_title,
            "type": "category"
        })
        
        # Add subsection nodes and connect to sections
        for subsection_name, items in section_data["subsections"].items():
            subsection_id = make_id(subsection_name)
            
            nodes.append({
                "id": subsection_id,
                "label": subsection_name,
                "type": "category"
            })
            
            # Connect subsection to section
            edges.append({
                "source": section_id,
                "target": subsection_id,
                "label": "contains"
            })
            
            # Add items as nodes and connect to subsections
            for item in items:
                item_name = item["name"]
                item_id = make_id(item_name)
                
                # Determine item type
                item_type = "person" if item_name in people else "concept"
                
                # Add item node if not already added
                if not any(node["id"] == item_id for node in nodes):
                    # Create node with basic info
                    node_data = {
                        "id": item_id,
                        "label": item_name,
                        "type": item_type
                    }
                    
                    # Add external_url if it exists in the item
                    if "external_url" in item:
                        node_data["external_url"] = item["external_url"]
                    
                    nodes.append(node_data)
                
                # Connect item to subsection
                edges.append({
                    "source": subsection_id,
                    "target": item_id,
                    "label": "includes"
                })
    
    # Add relationships between items in similar domains
    # This is a simplified approach to create related_to relationships
    processed_pairs = set()
    
    for section_id, section_data in structured_ontology.items():
        for subsection_name, items in section_data["subsections"].items():
            # Create relationships within the same subsection
            for i, item1 in enumerate(items):
                for item2 in items[i+1:]:
                    item1_id = make_id(item1["name"])
                    item2_id = make_id(item2["name"])
                    
                    # Create a canonical order for the pair to avoid duplicates
                    pair = tuple(sorted([item1_id, item2_id]))
                    
                    if pair not in processed_pairs:
                        processed_pairs.add(pair)
                        
                        # Add relationship edge
                        edges.append({
                            "source": item1_id,
                            "target": item2_id,
                            "label": "related_to"
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
    
    # Parse the markdown into a structured format
    structured_ontology = parse_markdown_ontology(markdown_text)
    
    # Convert to a knowledge graph format
    knowledge_graph = convert_to_knowledge_graph(structured_ontology)
    
    # Combine and save the results
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
        "section_sizes": {},
        "largest_sections": [],
        "most_connected_concepts": []
    }
    
    # Count subsections and concepts
    for section_id, section_data in structured_ontology.items():
        subsection_count = len(section_data["subsections"])
        analysis["total_subsections"] += subsection_count
        
        concept_count = 0
        for _, items in section_data["subsections"].items():
            concept_count += len(items)
        
        analysis["total_concepts"] += concept_count
        analysis["section_sizes"][section_id] = {
            "title": section_data["title"],
            "subsections": subsection_count,
            "concepts": concept_count
        }
    
    # Find the largest sections
    largest_sections = sorted(
        [(k, v["subsections"], v["concepts"], v["title"]) 
         for k, v in analysis["section_sizes"].items()],
        key=lambda x: (x[1], x[2]),
        reverse=True
    )[:3]
    
    analysis["largest_sections"] = [
        {"number": i+1, "id": num, "title": title, "subsections": subs, "concepts": concepts}
        for i, (num, subs, concepts, title) in enumerate(largest_sections)
    ]
    
    return analysis
