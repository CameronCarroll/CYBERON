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
- Shannon Entropy [url:/articles/shannon-entropy.html]: A mathematical measure of information content or uncertainty
- Channel Capacity: The maximum rate at which information can be transmitted over a communication channel

## Key Figures
- Claude Shannon: American mathematician, known as 'the father of information theory'
- Norbert Wiener [url:/people/wiener.html]: American mathematician who established the field of cybernetics

# Cybernetics

## Feedback Systems
- Negative Feedback: A type of feedback when the system responds to reduce the output signal
- Homeostasis: The ability of a system to maintain stability despite external changes

## Cybernetic Applications
- AI Systems [url:/applications/ai-systems.html]: Application of cybernetic principles to artificial intelligence
- Biological Systems: Study of regulatory mechanisms in living organisms
"""
        # Expected parsed structure
        self.expected_structure = {
            "information_theory": {
                "title": "Information Theory",
                "subsections": {
                    "Foundational Concepts": [
                        {"name": "Shannon Entropy", "description": "A mathematical measure of information content or uncertainty", "external_url": "/articles/shannon-entropy.html"},
                        {"name": "Channel Capacity", "description": "The maximum rate at which information can be transmitted over a communication channel"}
                    ],
                    "Key Figures": [
                        {"name": "Claude Shannon", "description": "American mathematician, known as 'the father of information theory'"},
                        {"name": "Norbert Wiener", "description": "American mathematician who established the field of cybernetics", "external_url": "/people/wiener.html"}
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
                        {"name": "AI Systems", "description": "Application of cybernetic principles to artificial intelligence", "external_url": "/applications/ai-systems.html"},
                        {"name": "Biological Systems", "description": "Study of regulatory mechanisms in living organisms"}
                    ]
                }
            }
        }

    def test_parse_markdown_ontology(self):
        """Test parsing markdown into structured ontology."""
        result = parse_markdown_ontology(self.sample_markdown)
        # Set maxDiff to None to see full difference if test fails
        self.maxDiff = None
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
        
        # Check for external_url in nodes
        found_url_nodes = []
        for node in knowledge_graph["nodes"]:
            if "external_url" in node:
                found_url_nodes.append(node["id"])
        
        # Should find external URLs for these nodes
        self.assertIn("shannon_entropy", found_url_nodes)
        self.assertIn("norbert_wiener", found_url_nodes)
        self.assertIn("ai_systems", found_url_nodes)
        
        # Check specific external URLs
        shannon_node = next(node for node in knowledge_graph["nodes"] if node["id"] == "shannon_entropy")
        self.assertEqual(shannon_node["external_url"], "/articles/shannon-entropy.html")
        
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
