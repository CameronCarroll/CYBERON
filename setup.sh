#!/bin/bash
# Script to set up the new markdown parser

set -e  # Exit on any error

# Define colors for prettier output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Markdown Parser Migration${NC}"


# Step 2: Create backup of original parser
echo -e "\n${YELLOW}Step 2: Creating backup of original parser${NC}"
if [ -f "app/utils/ontology_parser.py" ]; then
    cp app/utils/ontology_parser.py app/utils/ontology_parser.py.bak
    echo -e "${GREEN}Backup created at app/utils/ontology_parser.py.bak${NC}"
else
    echo -e "${RED}Original parser not found at app/utils/ontology_parser.py${NC}"
    exit 1
fi

# Step 3: Create the new parser
echo -e "\n${YELLOW}Step 3: Creating new parser implementation${NC}"
cat > app/utils/ontology_parser.py << 'EOF'
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
    
    # Convert markdown to HTML for easier parsing
    html = markdown.markdown(markdown_text)
    soup = BeautifulSoup(html, 'html.parser')
    
    structured_ontology = {}
    current_section = None
    current_subsection = None
    
    # Find all headings and list items
    elements = soup.find_all(['h1', 'h2', 'h3', 'li'])
    
    for element in elements:
        if element.name == 'h1':
            # Create a new top-level section
            section_title = element.text.strip()
            section_id = make_id(section_title)
            structured_ontology[section_id] = {
                "title": section_title,
                "subsections": {}
            }
            current_section = section_id
            current_subsection = None
        
        elif element.name == 'h2' and current_section:
            # Create a new subsection within the current section
            subsection_title = element.text.strip()
            structured_ontology[current_section]["subsections"][subsection_title] = []
            current_subsection = subsection_title
        
        elif element.name == 'h3' and current_section:
            # H3 headings are treated as specialized subsections
            # Depending on your requirements, you might want to handle these differently
            subsection_title = element.text.strip()
            structured_ontology[current_section]["subsections"][subsection_title] = []
            current_subsection = subsection_title
        
        elif element.name == 'li' and current_section and current_subsection:
            # Process list items as entities with descriptions
            item_text = element.text.strip()
            
            # Split item on the first colon to separate name and description
            parts = item_text.split(':', 1)
            if len(parts) == 2:
                name = parts[0].strip()
                description = parts[1].strip()
                
                structured_ontology[current_section]["subsections"][current_subsection].append({
                    "name": name,
                    "description": description
                })
            else:
                # Handle items without descriptions
                structured_ontology[current_section]["subsections"][current_subsection].append({
                    "name": item_text,
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
                item_name = item["name"]
                item_id = make_id(item_name)
                
                # Determine item type
                item_type = "person" if item_name in people else "concept"
                
                # Add item node if not already added
                if not any(node["id"] == item_id for node in nodes):
                    nodes.append({
                        "id": item_id,
                        "label": item_name,
                        "type": item_type
                    })
                
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
EOF
echo -e "${GREEN}New parser created at app/utils/ontology_parser.py${NC}"

# Step 4: Create the test file
echo -e "\n${YELLOW}Step 4: Creating test file${NC}"
mkdir -p app/tests
touch app/tests/__init__.py

cat > app/tests/test_ontology_parser.py << 'EOF'
import unittest
import json
import os
import tempfile
from unittest.mock import patch, mock_open
import pytest

# Import the updated parser module
from app.utils.ontology_parser import (
    parse_markdown_ontology,
    extract_entities,
    convert_to_knowledge_graph,
    extract_markdown_to_json
)


class TestMarkdownOntologyParser(unittest.TestCase):
    """Test suite for the markdown-based ontology parser."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample markdown input for testing
        self.sample_markdown = """
# Information Theory

## Foundational Concepts
- Shannon Entropy: A mathematical measure of information content or uncertainty
- Channel Capacity: The maximum rate at which information can be transmitted over a communication channel

## Key Figures
- Claude Shannon: American mathematician, known as 'the father of information theory'
- Norbert Wiener: American mathematician who established the field of cybernetics

# Cybernetics

## Feedback Systems
- Negative Feedback: A type of feedback when the system responds to reduce the output signal
- Homeostasis: The ability of a system to maintain stability despite external changes

## Cybernetic Applications
- AI Systems: Application of cybernetic principles to artificial intelligence
- Biological Systems: Study of regulatory mechanisms in living organisms
"""
        # Expected parsed structure
        self.expected_structure = {
            "information_theory": {
                "title": "Information Theory",
                "subsections": {
                    "Foundational Concepts": [
                        {"name": "Shannon Entropy", "description": "A mathematical measure of information content or uncertainty"},
                        {"name": "Channel Capacity", "description": "The maximum rate at which information can be transmitted over a communication channel"}
                    ],
                    "Key Figures": [
                        {"name": "Claude Shannon", "description": "American mathematician, known as 'the father of information theory'"},
                        {"name": "Norbert Wiener", "description": "American mathematician who established the field of cybernetics"}
                    ]
                }
            },
            "cybernetics": {
                "title": "Cybernetics",
                "subsections": {
                    "Feedback Systems": [
                        {"name": "Negative Feedback", "description": "A type of feedback when the system responds to reduce the output signal"},
                        {"name": "Homeostasis", "description": "The ability of a system to maintain stability despite external changes"}
                    ],
                    "Cybernetic Applications": [
                        {"name": "AI Systems", "description": "Application of cybernetic principles to artificial intelligence"},
                        {"name": "Biological Systems", "description": "Study of regulatory mechanisms in living organisms"}
                    ]
                }
            }
        }

    def test_parse_markdown_ontology(self):
        """Test parsing markdown into structured ontology."""
        result = parse_markdown_ontology(self.sample_markdown)
        self.assertEqual(result, self.expected_structure)

    def test_extract_entities(self):
        """Test extracting entities (concepts, people) from structured ontology."""
        people, concepts, domains = extract_entities(self.expected_structure)
        
        # Check people extraction
        expected_people = {"Claude Shannon", "Norbert Wiener"}
        self.assertEqual(people, expected_people)
        
        # Check concepts extraction
        expected_concepts = {
            "Shannon Entropy", "Channel Capacity", 
            "Negative Feedback", "Homeostasis", 
            "AI Systems", "Biological Systems"
        }
        self.assertEqual(concepts, expected_concepts)
        
        # Check domain structure (not testing exact values because order might vary)
        self.assertEqual(len(domains), 4)  # Should have 4 domain sections

    def test_convert_to_knowledge_graph(self):
        """Test converting structured ontology to knowledge graph."""
        knowledge_graph = convert_to_knowledge_graph(self.expected_structure)
        
        # Check if both nodes and edges exist
        self.assertIn("nodes", knowledge_graph)
        self.assertIn("edges", knowledge_graph)
        
        # Check nodes count
        self.assertEqual(len(knowledge_graph["nodes"]), 14)
        
        # Check specific nodes existence
        node_ids = [node["id"] for node in knowledge_graph["nodes"]]
        self.assertIn("information_theory", node_ids)
        self.assertIn("claude_shannon", node_ids)
        self.assertIn("cybernetics", node_ids)
        
        # Check edges count (base relationship connections)
        # The exact number may vary based on implementation details
        self.assertGreaterEqual(len(knowledge_graph["edges"]), 12)
        
        # Check specific relationships
        found_information_theory_to_foundational = False
        for edge in knowledge_graph["edges"]:
            if (edge["source"] == "information_theory" and 
                edge["target"] == "foundational_concepts" and 
                edge["label"] == "contains"):
                found_information_theory_to_foundational = True
                break
        
        self.assertTrue(found_information_theory_to_foundational)

    def test_extract_markdown_to_json(self):
        """Test end-to-end conversion from markdown to JSON."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_input:
            temp_input.write(self.sample_markdown)
            temp_input_path = temp_input.name
        
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_output:
            temp_output_path = temp_output.name
        
        try:
            # Run the conversion
            extract_markdown_to_json(temp_input_path, temp_output_path)
            
            # Load the output and verify
            with open(temp_output_path, 'r') as f:
                result = json.load(f)
            
            # Check structure keys
            self.assertIn("structured_ontology", result)
            self.assertIn("knowledge_graph", result)
            
            # Check ontology sections
            structured_ontology = result["structured_ontology"]
            self.assertIn("information_theory", structured_ontology)
            self.assertIn("cybernetics", structured_ontology)
            
            # Check knowledge graph nodes and edges
            knowledge_graph = result["knowledge_graph"]
            self.assertIn("nodes", knowledge_graph)
            self.assertIn("edges", knowledge_graph)
        finally:
            # Clean up temp files
            os.unlink(temp_input_path)
            os.unlink(temp_output_path)

    def test_complex_markdown_parsing(self):
        """Test handling of more complex markdown with nested hierarchies."""
        complex_markdown = """
# Complex Domain

## Level 1 Subsection
- Item A: Description A
  - Subitem A1: Nested description
  - Subitem A2: Another nested description
- Item B: Description B

## Level 1 Subsection 2
- Item C: Description C

### Level 2 Subsection
- Item D: Description D
- Item E: Description E
"""
        # This test verifies the parser can handle nested structures
        # The exact expectations would depend on how you implement the parser
        result = parse_markdown_ontology(complex_markdown)
        self.assertIn("complex_domain", result)
        self.assertIn("Level 1 Subsection", result["complex_domain"]["subsections"])
        
        # Check if nested items are properly handled (implementation dependent)
        level1_subsection = result["complex_domain"]["subsections"]["Level 1 Subsection"]
        self.assertTrue(any("Item A" in item.get("name", "") for item in level1_subsection))

    def test_malformed_markdown(self):
        """Test handling of malformed markdown input."""
        malformed_markdown = """
No top-level heading

## Orphaned subsection
- Item without context
"""
        # Test should verify the parser handles malformed input gracefully
        # Depending on implementation, could raise an exception or provide partial results
        with self.assertRaises(ValueError):
            parse_markdown_ontology(malformed_markdown)

    def test_empty_input(self):
        """Test handling of empty input."""
        empty_markdown = ""
        result = parse_markdown_ontology(empty_markdown)
        self.assertEqual(result, {})

    def test_id_generation(self):
        """Test that IDs are properly generated from titles."""
        # This tests that titles like "Complex Name With Spaces" 
        # become ids like "complex_name_with_spaces"
        simple_markdown = """
# Test Title With Spaces

## Subsection With Spaces
- Item: Description
"""
        result = parse_markdown_ontology(simple_markdown)
        self.assertIn("test_title_with_spaces", result)
        self.assertIn("Subsection With Spaces", result["test_title_with_spaces"]["subsections"])

    def test_concepts_vs_people_detection(self):
        """Test proper identification of concept vs. person entities."""
        person_detection_markdown = """
# Test Domain

## Key Figures
- John Doe: A test person
- Jane Smith: Another test person

## Concepts
- Test Concept: A concept description
"""
        structured = parse_markdown_ontology(person_detection_markdown)
        people, concepts, _ = extract_entities(structured)
        
        self.assertIn("John Doe", people)
        self.assertIn("Jane Smith", people)
        self.assertIn("Test Concept", concepts)
        self.assertNotIn("John Doe", concepts)
        self.assertNotIn("Test Concept", people)


# Run the tests
if __name__ == '__main__':
    unittest.main()
EOF
echo -e "${GREEN}Test file created at app/tests/test_ontology_parser.py${NC}"

# Step 5: Create migration script
echo -e "\n${YELLOW}Step 5: Creating migration script${NC}"
cat > migrate_parser_functions.py << 'EOF'
#!/usr/bin/env python3
"""
Script to migrate application code from old parser function names to new ones.
Updates imports and function calls in all Python files in the project.
"""

import os
import re
from pathlib import Path

# Define replacement patterns
REPLACEMENTS = [
    # Function name replacements
    (r'extract_text_to_json\(', 'extract_markdown_to_json('),
    (r'parse_ontology_text\(', 'parse_markdown_ontology('),
    
    # Import replacements
    (r'from app\.utils\.ontology_parser import extract_text_to_json', 
     'from app.utils.ontology_parser import extract_markdown_to_json'),
    (r'from app\.utils\.ontology_parser import parse_ontology_text', 
     'from app.utils.ontology_parser import parse_markdown_ontology'),
    
    # Combined import replacements
    (r'from app\.utils\.ontology_parser import (.*?)extract_text_to_json(.*?)', 
     r'from app.utils.ontology_parser import \1extract_markdown_to_json\2'),
    (r'from app\.utils\.ontology_parser import (.*?)parse_ontology_text(.*?)', 
     r'from app.utils.ontology_parser import \1parse_markdown_ontology\2'),
]

def update_file(file_path):
    """Update a single file, replacing old function names with new ones."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    for pattern, replacement in REPLACEMENTS:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        print(f"Updating {file_path}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def find_and_update_files(root_dir):
    """Find and update all Python files in the project."""
    root_path = Path(root_dir)
    python_files = list(root_path.glob('**/*.py'))
    
    updated_count = 0
    for file_path in python_files:
        # Skip the ontology_parser.py file itself
        if file_path.name == 'ontology_parser.py':
            continue
            
        if update_file(file_path):
            updated_count += 1
    
    return updated_count

def main():
    """Main function to run the migration."""
    # Get the project root directory
    project_root = os.path.abspath(os.path.dirname(__file__))
    
    print(f"Scanning Python files in {project_root}")
    updated_count = find_and_update_files(project_root)
    
    print(f"Updated {updated_count} files with new function names")
    print("Migration complete.")

if __name__ == '__main__':
    main()
EOF
chmod +x migrate_parser_functions.py
echo -e "${GREEN}Migration script created at migrate_parser_functions.py${NC}"

# Step 6: Run the migration
echo -e "\n${YELLOW}Step 6: Running the migration script${NC}"
python3 migrate_parser_functions.py

# Step 7: Run the tests
echo -e "\n${YELLOW}Step 7: Running the tests${NC}"
python -m pytest app/tests/test_ontology_parser.py -v

echo -e "\n${GREEN}Migration complete!${NC}"
echo -e "Your application now uses the new markdown-based parser."
echo -e "If you need to restore the original parser, you can find it at:"
echo -e "app/utils/ontology_parser.py.bak"

echo -e "\n${YELLOW}What to do next:${NC}"
echo -e "1. Test your application with the new parser"
echo -e "2. Update your upload functionality to accept markdown files (.md)"
echo -e "3. Update your documentation to reflect the new markdown format"