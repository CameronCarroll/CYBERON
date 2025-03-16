import re
import json
from typing import Dict, List, Set, Tuple

def parse_ontology_text(text: str) -> Dict:
    """
    Parse the ontology text document into a structured dictionary
    """
    # Split text into sections based on numbered headings
    section_pattern = r'\n(\d+\.\s+[^\n]+)\n'
    sections = re.split(section_pattern, text)
    
    # The first element is the header before any numbered sections
    header = sections.pop(0).strip()
    
    structured_ontology = {}
    
    # Process each section
    for i in range(0, len(sections), 2):
        if i + 1 < len(sections):
            section_title = sections[i].strip()
            section_content = sections[i + 1].strip()
            
            # Extract section number and title
            match = re.match(r'(\d+)\.\s+(.+)', section_title)
            if match:
                section_num = int(match.group(1))
                section_name = match.group(2)
                
                # Parse subsections
                subsections = parse_subsections(section_content)
                
                structured_ontology[section_num] = {
                    "title": section_name,
                    "subsections": subsections
                }
    
    return structured_ontology

def parse_subsections(section_content: str) -> Dict:
    """
    Parse subsections within a main section
    """
    # Split by double newlines to separate subsections
    blocks = re.split(r'\n\n+', section_content)
    subsections = {}
    
    for block in blocks:
        lines = block.strip().split('\n')
        if not lines:
            continue
            
        # First line is the subsection title
        subsection_title = lines[0].strip()
        items = []
        
        # Remaining lines are the items
        for line in lines[1:]:
            line = line.strip()
            if line:
                items.append(line)
        
        if subsection_title and items:
            subsections[subsection_title] = items
    
    return subsections

def extract_entities(structured_ontology: Dict) -> Tuple[Set[str], Set[str], Dict[str, List[str]]]:
    """
    Extract people, concepts, and domains from the structured ontology
    """
    people = set()
    concepts = set()
    domains = {}
    
    # Extract people from Key Figures sections
    for section_num, section_data in structured_ontology.items():
        for subsection_name, items in section_data["subsections"].items():
            if "Key Figures" in subsection_name or "Figures" in subsection_name:
                for item in items:
                    people.add(item)
            elif "Principles" in subsection_name or "Concepts" in subsection_name:
                for item in items:
                    concepts.add(item)
            
            # Store items by subsection for domain organization
            domain_name = f"{section_data['title']} - {subsection_name}"
            domains[domain_name] = items
    
    return people, concepts, domains

def convert_to_knowledge_graph(structured_ontology: Dict) -> Dict:
    """
    Convert the structured ontology into a knowledge graph format
    """
    people, concepts, domains_items = extract_entities(structured_ontology)
    
    # Create nodes
    nodes = []
    edges = []
    
    # Helper function to create a clean ID
    def make_id(text):
        return re.sub(r'[^a-z0-9_]', '_', text.lower())
    
    # Add section nodes
    for section_num, section_data in structured_ontology.items():
        section_id = f"section_{section_num}"
        section_title = section_data["title"]
        
        nodes.append({
            "id": section_id,
            "label": section_title,
            "type": "domain"
        })
        
        # Add subsection nodes and connect to sections
        for subsection_name, items in section_data["subsections"].items():
            subsection_id = make_id(f"{section_title}_{subsection_name}")
            
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
                item_id = make_id(item)
                
                # Determine item type
                item_type = "person" if item in people else "concept"
                
                # Add item node if not already added
                if not any(node["id"] == item_id for node in nodes):
                    nodes.append({
                        "id": item_id,
                        "label": item,
                        "type": item_type
                    })
                
                # Connect item to subsection
                edges.append({
                    "source": subsection_id,
                    "target": item_id,
                    "label": "includes"
                })
    
    # Add relationships between concepts based on co-occurrence
    for domain, items in domains_items.items():
        # Connect items within the same domain
        for i, item1 in enumerate(items):
            for item2 in items[i+1:]:
                item1_id = make_id(item1)
                item2_id = make_id(item2)
                
                edges.append({
                    "source": item1_id,
                    "target": item2_id,
                    "label": "related_to"
                })
    
    return {
        "nodes": nodes,
        "edges": edges
    }

def extract_text_to_json(input_file, output_file):
    """
    Process an ontology text file and save as structured JSON
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        ontology_text = f.read()
    
    # Parse the text into a structured format
    structured_ontology = parse_ontology_text(ontology_text)
    
    # Convert to a knowledge graph format
    knowledge_graph = convert_to_knowledge_graph(structured_ontology)
    
    # Save the results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "structured_ontology": structured_ontology,
            "knowledge_graph": knowledge_graph
        }, f, indent=2)
    
    print(f"Ontology processed and saved to {output_file}")
    print(f"Found {len(knowledge_graph['nodes'])} nodes and {len(knowledge_graph['edges'])} relationships")

def analyze_ontology_structure(structured_ontology):
    """
    Analyze the structure of the ontology for insights
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
    concept_connections = {}
    
    for section_num, section_data in structured_ontology.items():
        subsection_count = len(section_data["subsections"])
        analysis["total_subsections"] += subsection_count
        
        concept_count = 0
        for subsection, items in section_data["subsections"].items():
            concept_count += len(items)
        
        analysis["total_concepts"] += concept_count
        analysis["section_sizes"][section_num] = {
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
        {"number": num, "title": title, "subsections": subs, "concepts": concepts}
        for num, subs, concepts, title in largest_sections
    ]
    
    return analysis

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "ontology.txt"
        
    output_file = "cybernetics_ontology_processed.json"
    
    try:
        extract_text_to_json(input_file, output_file)
        
        # Load the processed data for analysis
        with open(output_file, 'r', encoding='utf-8') as f:
            processed_data = json.load(f)
        
        # Analyze the structure
        analysis = analyze_ontology_structure(processed_data["structured_ontology"])
        
        print("\nOntology Analysis:")
        print(f"Total sections: {analysis['section_count']}")
        print(f"Total subsections: {analysis['total_subsections']}")
        print(f"Total concepts: {analysis['total_concepts']}")
        
        print("\nLargest sections:")
        for section in analysis["largest_sections"]:
            print(f"  {section['number']}. {section['title']}: {section['subsections']} subsections, {section['concepts']} concepts")
            
    except Exception as e:
        print(f"Error processing ontology: {str(e)}")