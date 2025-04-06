import unittest
import tempfile
import os
import json
from typing import Dict, List, Set, Tuple, Any, Optional

# Assume the refactored code is in 'app.utils.ontology_parser'
# Adjust the import path if your file structure is different
try:
    from app.utils.ontology_parser import (
        make_id,
        parse_markdown_ontology,
        convert_to_knowledge_graph,
        extract_markdown_to_json,
        # Import analysis functions if they exist and are tested separately or implicitly
        # analyze_ontology_structure,
        # extract_entities
    )
except ImportError:
    # Fallback if the exact path doesn't exist, useful for local testing
    # Make sure the refactored ontology_parser.py is in the same directory or accessible
    print("Warning: Could not import from 'app.utils.ontology_parser'. Trying local import.")
    # Make sure the refactored 'ontology_parser.py' is in the same directory or Python path
    from ontology_parser import (
        make_id,
        parse_markdown_ontology,
        convert_to_knowledge_graph,
        extract_markdown_to_json
    )


# --- Helper function to find nodes/edges easily in tests ---
def find_node_by_id(nodes: List[Dict], node_id: str) -> Optional[Dict]:
    """Finds a node in a list of nodes by its ID."""
    return next((node for node in nodes if node.get("id") == node_id), None)

def get_edges_as_set(edges: List[Dict]) -> Set[Tuple[str, str, str]]:
    """Converts a list of edge dictionaries to a set of (source, target, label) tuples."""
    # Use empty string defaults for robustness against missing keys
    return {(edge.get("source", ""), edge.get("target", ""), edge.get("label", "")) for edge in edges}

# --- Test Class Updated for Phase 2 ---
class TestHierarchicalMarkdownOntologyParser(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures with hierarchical markdown."""
        self.sample_hierarchical_markdown = """
# Science

Top-level category for scientific domains.

## Biology

The study of life and living organisms.

### Zoology

The branch of biology that studies the animal kingdom.

- Entity: Lion
  Description: A large cat species native to Africa and India.
  Type: Species
  Attributes:
    - Attribute: Conservation Status [url:https://www.iucnredlist.org/species/15951/50659042]
      Value: Vulnerable
    - Attribute: Average Weight (kg)
      Value: 190
  Relationships:
    - Relationship: prey
      Target: Zebra
    - Relationship: classification
      Target: Mammal # Defined later under Zoology

- Entity: Zebra
  Description: An African equine known for stripes.
  Type: Species

- Entity: Mammal
  Description: A class of warm-blooded vertebrates.
  Type: Class # This entity belongs to Zoology

### Botany

The scientific study of plants.

- Entity: Oak Tree
  Description: A tree or shrub in the genus Quercus.
  Type: Plant
  Attributes:
    - Attribute: Leaf Type
      Value: Broadleaf

## Chemistry

Study of substances and their properties.

- Entity: Water
  Type: Molecule
  Attributes:
    - Attribute: Formula
      Value: H2O
  Relationships:
    - Relationship: example_of
      Target: Molecule # Target defined later

# Concepts

General concepts used across domains.

- Entity: Molecule
  Description: An electrically neutral group of two or more atoms held together by chemical bonds.
  Type: AbstractConcept

"""
        # --- Expected structure after parsing ---
        # (Removed verbose expected_parsed_structure for brevity, tests verify key aspects)

        # --- Expected structure after conversion to Knowledge Graph ---
        self.expected_kg_node_ids = {
            # Categories
            "science", "biology", "zoology", "botany", "chemistry", "concepts",
            # Entities
            "lion", "zebra", "mammal", "oak_tree", "water", "molecule"
        }
        # Example: Expected Lion node structure in KG
        self.expected_kg_lion_node = {
            "id": "lion",
            "label": "Lion",
            "type": "Species",
            "description": "A large cat species native to Africa and India.",
            "attributes": {
                "conservation_status": {
                    "value": "Vulnerable",
                    "url": "https://www.iucnredlist.org/species/15951/50659042"
                },
                "average_weight_kg": { # Note: ID generation includes units if in name
                    "value": "190",
                    "url": None
                }
            }
        }
        # Expected Edges (source_id, target_id, label)
        self.expected_kg_edges = {
            # Hierarchy Edges
            ("science", "biology", "has_subcategory"),
            ("science", "chemistry", "has_subcategory"),
            ("biology", "zoology", "has_subcategory"),
            ("biology", "botany", "has_subcategory"),
            # Membership Edges
            ("lion", "zoology", "belongs_to_category"),
            ("zebra", "zoology", "belongs_to_category"),
            ("mammal", "zoology", "belongs_to_category"),
            ("oak_tree", "botany", "belongs_to_category"),
            ("water", "chemistry", "belongs_to_category"),
            ("molecule", "concepts", "belongs_to_category"),
            # Entity-to-Entity Edges
            ("lion", "zebra", "prey"),
            ("lion", "mammal", "classification"),
            ("water", "molecule", "example_of"),
        }

    def test_make_id(self):
        """Test the make_id utility function."""
        self.assertEqual("test_name", make_id("Test Name"))
        self.assertEqual("test_name", make_id("Test-Name"))
        self.assertEqual("h2o", make_id("H2O"))
        # FIX: Corrected expectation based on function logic (multiple non-alpha -> single underscore)
        self.assertEqual("a_b", make_id("A & B"))
        self.assertEqual("test_kg", make_id("Test (kg)"))
        self.assertEqual("leading_trailing", make_id("_Leading Trailing_"))

    def test_parse_markdown_ontology_hierarchical(self):
        """Test parsing hierarchical markdown into the nested tree structure."""
        parsed_tree = parse_markdown_ontology(self.sample_hierarchical_markdown)

        # Check root structure
        self.assertIsInstance(parsed_tree, list)
        self.assertEqual(len(parsed_tree), 2, "Should have 2 root categories (Science, Concepts)")

        # Find Science root node
        science_node = next((n for n in parsed_tree if n.get("id") == "science"), None)
        self.assertIsNotNone(science_node)
        self.assertEqual(science_node.get("label"), "Science")
        self.assertEqual(science_node.get("level"), 1)
        self.assertEqual(len(science_node.get("children", [])), 2, "Science should have 2 children (Biology, Chemistry)")
        self.assertEqual(len(science_node.get("entities", [])), 0)

        # Find Biology node
        biology_node = next((n for n in science_node["children"] if n.get("id") == "biology"), None)
        self.assertIsNotNone(biology_node)
        self.assertEqual(biology_node.get("level"), 2)
        self.assertEqual(len(biology_node.get("children", [])), 2, "Biology should have 2 children (Zoology, Botany)")
        self.assertEqual(len(biology_node.get("entities", [])), 0)

        # Find Zoology node
        zoology_node = next((n for n in biology_node["children"] if n.get("id") == "zoology"), None)
        self.assertIsNotNone(zoology_node)
        self.assertEqual(zoology_node.get("level"), 3)
        self.assertEqual(len(zoology_node.get("children", [])), 0)
        self.assertEqual(len(zoology_node.get("entities", [])), 3, "Zoology should have 3 entities")

        # Find Lion entity data within Zoology
        lion_entity_data = next((e for e in zoology_node["entities"] if e.get("name") == "Lion"), None)
        self.assertIsNotNone(lion_entity_data)
        self.assertEqual(lion_entity_data.get("type"), "Species")
        self.assertEqual(len(lion_entity_data.get("attributes", [])), 2)
        # Check a specific attribute
        conservation_attr = lion_entity_data["attributes"][0]
        self.assertEqual(conservation_attr.get("name"), "Conservation Status")
        self.assertEqual(conservation_attr.get("value"), "Vulnerable")
        self.assertTrue(conservation_attr.get("url", "").startswith("https://"))
        self.assertEqual(len(lion_entity_data.get("relationships", [])), 2)
        # Check a specific relationship
        prey_rel = lion_entity_data["relationships"][0]
        self.assertEqual(prey_rel.get("type"), "prey")
        self.assertEqual(prey_rel.get("target"), "Zebra")

        # Check Concepts root node
        concepts_node = next((n for n in parsed_tree if n.get("id") == "concepts"), None)
        self.assertIsNotNone(concepts_node)
        self.assertEqual(concepts_node.get("level"), 1)
        self.assertEqual(len(concepts_node.get("children", [])), 0)
        self.assertEqual(len(concepts_node.get("entities", [])), 1, "Concepts should have 1 entity (Molecule)")
        molecule_entity_data = concepts_node["entities"][0]
        self.assertEqual(molecule_entity_data.get("name"), "Molecule")

    def test_convert_to_knowledge_graph_hierarchical(self):
        """Test converting the hierarchical tree to the KG format."""
        parsed_tree = parse_markdown_ontology(self.sample_hierarchical_markdown)
        knowledge_graph = convert_to_knowledge_graph(parsed_tree)

        self.assertIn("nodes", knowledge_graph)
        self.assertIn("edges", knowledge_graph)

        nodes = knowledge_graph["nodes"]
        edges = knowledge_graph["edges"]

        # Check Node Count and IDs
        self.assertEqual(len(nodes), len(self.expected_kg_node_ids), "Unexpected number of nodes")
        actual_node_ids = {node["id"] for node in nodes}
        self.assertEqual(actual_node_ids, self.expected_kg_node_ids, "Node IDs do not match expected IDs")

        # Check Category Node Structure (Example: Biology)
        biology_kg_node = find_node_by_id(nodes, "biology")
        self.assertIsNotNone(biology_kg_node)
        self.assertEqual(biology_kg_node.get("label"), "Biology")
        self.assertEqual(biology_kg_node.get("type"), "Category")
        self.assertEqual(biology_kg_node.get("attributes"), {}, "Category nodes should have empty attributes dict")

        # Check Entity Node Structure (Example: Lion)
        lion_kg_node = find_node_by_id(nodes, "lion")
        self.assertIsNotNone(lion_kg_node)
        self.assertEqual(lion_kg_node.get("label"), self.expected_kg_lion_node["label"])
        self.assertEqual(lion_kg_node.get("type"), self.expected_kg_lion_node["type"])
        self.assertEqual(lion_kg_node.get("description"), self.expected_kg_lion_node["description"])
        # Deep check of nested attributes dictionary
        self.assertDictEqual(lion_kg_node.get("attributes", {}), self.expected_kg_lion_node["attributes"])

        # Check another entity (Water)
        water_kg_node = find_node_by_id(nodes, "water")
        self.assertIsNotNone(water_kg_node)
        self.assertEqual(water_kg_node.get("type"), "Molecule")
        self.assertEqual(water_kg_node.get("attributes", {}).get("formula", {}).get("value"), "H2O")
        self.assertIsNone(water_kg_node.get("attributes", {}).get("formula", {}).get("url"))

        # Check Edges
        self.assertEqual(len(edges), len(self.expected_kg_edges), "Unexpected number of edges")
        actual_edge_set = get_edges_as_set(edges)
        self.assertEqual(actual_edge_set, self.expected_kg_edges, "Edges do not match expected edges")

    def test_extract_markdown_to_json_hierarchical(self):
        """Test end-to-end conversion from hierarchical markdown to JSON."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".md", encoding='utf-8') as temp_input:
            temp_input.write(self.sample_hierarchical_markdown)
            temp_input_path = temp_input.name

        # Create a temporary file path for output, ensure it doesn't exist yet
        temp_output_fd, temp_output_path = tempfile.mkstemp(suffix=".json")
        os.close(temp_output_fd) # Close the file descriptor, we just want the path

        try:
            # Execute the main function
            extract_markdown_to_json(temp_input_path, temp_output_path)

            # Load and verify the output JSON
            self.assertTrue(os.path.exists(temp_output_path), "Output JSON file was not created.")
            with open(temp_output_path, 'r', encoding='utf-8') as f:
                result = json.load(f)

            # Check top-level keys
            self.assertIn("knowledge_graph", result)
            self.assertIn("analysis", result)

            knowledge_graph = result["knowledge_graph"]
            self.assertIn("nodes", knowledge_graph)
            self.assertIn("edges", knowledge_graph)

            # Verify KG structure within JSON
            nodes = knowledge_graph["nodes"]
            edges = knowledge_graph["edges"]
            self.assertEqual(len(nodes), len(self.expected_kg_node_ids))
            actual_node_ids = {node["id"] for node in nodes}
            self.assertEqual(actual_node_ids, self.expected_kg_node_ids)

            # Spot check a node
            oak_node = find_node_by_id(nodes, "oak_tree")
            self.assertIsNotNone(oak_node)
            self.assertEqual(oak_node.get("label"), "Oak Tree")
            self.assertEqual(oak_node.get("attributes", {}).get("leaf_type", {}).get("value"), "Broadleaf")

            # Spot check edges
            actual_edge_set = get_edges_as_set(edges)
            self.assertIn(("lion", "zoology", "belongs_to_category"), actual_edge_set)
            self.assertIn(("biology", "botany", "has_subcategory"), actual_edge_set)

            # Verify analysis structure
            analysis = result["analysis"]
            self.assertGreaterEqual(analysis.get("total_categories", 0), 6) # Science, Bio, Zoo, Bot, Chem, Concepts
            self.assertGreaterEqual(analysis.get("total_entities", 0), 6) # Lion, Zeb, Mam, Oak, Wat, Mol
            self.assertEqual(analysis.get("max_depth", 0), 3)

        finally:
            # Clean up temporary files
            if os.path.exists(temp_input_path):
                 os.unlink(temp_input_path)
            if os.path.exists(temp_output_path):
                 os.unlink(temp_output_path)


    def test_malformed_markdown_handling(self):
        """Test handling of malformed or edge-case markdown input."""
        # Empty input
        empty_markdown = ""
        parsed_tree = parse_markdown_ontology(empty_markdown)
        self.assertEqual(parsed_tree, [], "Parsing empty string should yield empty list")
        kg = convert_to_knowledge_graph(parsed_tree)
        self.assertEqual(kg, {"nodes": [], "edges": []}, "KG from empty parse should be empty")

        # Orphaned entity (no section header) - should be skipped by parser
        orphaned_entity = "\n- Entity: Orphan\n  Description: Lost\n"
        # Parser should log a warning (check console output if needed) and skip entity
        parsed_tree = parse_markdown_ontology(orphaned_entity)
        self.assertEqual(parsed_tree, [], "Parsing orphaned entity should yield empty list")
        kg = convert_to_knowledge_graph(parsed_tree)
        self.assertEqual(kg, {"nodes": [], "edges": []}, "KG from orphaned entity parse should be empty")

        # Malformed attribute/relationship pairs (should be skipped by parser)
        # FIX: Modified comments to not start with '# ' to avoid misinterpretation as headings
        malformed = """
# Test Section
- Entity: TestEnt
  Attributes:
  - Attribute: Attr1
    ; Missing Value: line
  - Attribute: Attr2
    Value: Val2 # Correct pair
  Relationships:
  - Relationship: Rel1
    ; Missing Target: line
  - Relationship: Rel2
    Target: SomeTarget # Correct pair
"""
        parsed = parse_markdown_ontology(malformed)
        # Check that only the correctly formed pairs were parsed
        # There should be one root category node
        self.assertEqual(len(parsed), 1, "Malformed test should yield one root category node")

        # Check the content of the parsed structure
        self.assertEqual(parsed[0]['id'], 'test_section')
        test_entities = parsed[0].get("entities", [])
        self.assertEqual(len(test_entities), 1, "Should have parsed one entity in Test Section")
        test_ent_data = test_entities[0]
        self.assertEqual(test_ent_data['name'], 'TestEnt')

        # Verify only the valid attribute was parsed
        self.assertEqual(len(test_ent_data.get("attributes", [])), 1, "Should only parse valid attribute")
        self.assertEqual(test_ent_data["attributes"][0]["name"], "Attr2")
        self.assertEqual(test_ent_data["attributes"][0]["value"], "Val2")

        # Verify only the valid relationship was parsed
        self.assertEqual(len(test_ent_data.get("relationships", [])), 1, "Should only parse valid relationship")
        self.assertEqual(test_ent_data["relationships"][0]["type"], "Rel2")
        self.assertEqual(test_ent_data["relationships"][0]["target"], "SomeTarget")

        # Convert and check KG - ensures conversion handles the correctly parsed subset
        kg = convert_to_knowledge_graph(parsed)
        self.assertIn("nodes", kg)
        self.assertIn("edges", kg)

        # Check nodes: Test Section, TestEnt, SomeTarget (placeholder)
        self.assertEqual(len(kg.get("nodes", [])), 3)
        actual_node_ids = {n['id'] for n in kg['nodes']}
        self.assertEqual(actual_node_ids, {'test_section', 'testent', 'sometarget'})

        test_ent_node = find_node_by_id(kg["nodes"], "testent")
        self.assertIsNotNone(test_ent_node)
        # Check nested attributes dict in KG node
        self.assertEqual(len(test_ent_node.get("attributes", {})), 1)
        self.assertIn("attr2", test_ent_node["attributes"])
        self.assertEqual(test_ent_node["attributes"]["attr2"]["value"], "Val2")
        self.assertIsNone(test_ent_node["attributes"]["attr2"]["url"])

        # Check edges: TestEnt -> TestSection, TestEnt -> SomeTarget
        self.assertEqual(len(kg.get("edges", [])), 2)
        actual_edges = get_edges_as_set(kg["edges"])
        self.assertIn(("testent", "test_section", "belongs_to_category"), actual_edges)
        self.assertIn(("testent", "sometarget", "Rel2"), actual_edges)


if __name__ == '__main__':
    # Ensure the script can find the ontology_parser module if run directly
    # You might need to adjust sys.path depending on your project structure
    # import sys
    # sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'utils'))) # Example adjustment

    unittest.main(argv=['first-arg-is-ignored'], exit=False)