import re
import json
from typing import Dict, List, Set, Tuple, Any, Optional
import unittest
import tempfile
import os

# Import the real implementation from the ontology parser
from app.utils.ontology_parser import make_id, parse_markdown_ontology, convert_to_knowledge_graph, extract_markdown_to_json

# --- This is a helper function for the tests ---
def extract_entities_and_relationships(parsed_ontology):
     entities = {}
     relationships = []
     for section_id, section_data in parsed_ontology.items():
         for entity in section_data.get("entities", []):
             entity_name = entity.get("name")
             entities[entity_name] = {"type": entity.get("type"), "description": entity.get("description")}
             for rel in entity.get("relationships", []):
                 if rel.get("target") and rel.get("type"):
                      relationships.append({"source": entity_name, "target": rel["target"], "type": rel["type"]})
     return entities, relationships


# --- Test Class ---
class TestNewMarkdownOntologyParser(unittest.TestCase):
    # --- setUp with sample data ---
    def setUp(self):
        """Set up test fixtures with the NEW format."""
        # Important: 
        # 1. Parser ignores H2 headings (##), so entities must be directly under H1 headings (#)
        # 2. Entity lines must use exactly '- Entity:' (not '-  Entity:' with extra spaces)
        self.sample_markdown = """
# Biology

- Entity: Human
  Description: A bipedal primate capable of complex thought.
  Type: Species
  Attributes:
    - Attribute: Average Height
      Value: 1.7 meters
    - Attribute: Lifespan
      Value: 80 years
    - Attribute: Cognitive Ability [url:/docs/cognition]
      Value: High
  Relationships:
    - Relationship: has_part
      Target: Brain
    - Relationship: member_of
      Target: Mammal
    - Relationship: eats
      Target: Apple
    - Relationship: eats
      Target: Food # Generic Food relationship

- Entity: Brain
  Description: The central organ of the nervous system.
  Type: Organ
  Relationships:
    - Relationship: part_of
      Target: Human

- Entity: Mammal
  Description: A class of warm-blooded vertebrates.
  Type: Class

# Food

- Entity: Apple
  Description: A type of fruit, typically red or green.
  Type: Food
  Attributes:
    - Attribute: Color
      Value: Red/Green
    - Attribute: Nutritional Info [url:/nutrition/apple]
      Value: Rich in vitamins
  Relationships:
    - Relationship: eaten_by
      Target: Human

- Entity: Food
  Description: Any substance consumed to provide nutritional support.
  Type: Concept
"""
        self.expected_node_ids = {"human", "brain", "mammal", "apple", "food", "biology"}
        self.expected_human_attr_keys = {"average_height", "lifespan", "cognitive_ability", "cognitive_ability_url"}
        self.expected_apple_attr_keys = {"color", "nutritional_info", "nutritional_info_url"}

    def test_parse_markdown_ontology(self):
        """Test parsing NEW markdown format into structured ontology."""
        result = parse_markdown_ontology(self.sample_markdown)
        self.maxDiff = None
        
        # Verify the basic structure
        self.assertIn("biology", result)
        self.assertEqual("Biology", result["biology"]["title"])
        self.assertIn("entities", result["biology"])
        
        self.assertIn("food", result)
        self.assertEqual("Food", result["food"]["title"])
        self.assertIn("entities", result["food"])
        
        # Check the entities list
        biology_entities = result["biology"]["entities"]
        food_entities = result["food"]["entities"]
        
        self.assertEqual(3, len(biology_entities), "Biology section should have 3 entities")
        self.assertEqual(2, len(food_entities), "Food section should have 2 entities")
        
        # Find specific entities
        human = next((e for e in biology_entities if e["name"] == "Human"), None)
        brain = next((e for e in biology_entities if e["name"] == "Brain"), None)
        mammal = next((e for e in biology_entities if e["name"] == "Mammal"), None)
        apple = next((e for e in food_entities if e["name"] == "Apple"), None)
        food = next((e for e in food_entities if e["name"] == "Food"), None)
        
        # Verify all entities were found
        self.assertIsNotNone(human, "Human entity should exist")
        self.assertIsNotNone(brain, "Brain entity should exist")
        self.assertIsNotNone(mammal, "Mammal entity should exist")
        self.assertIsNotNone(apple, "Apple entity should exist")
        self.assertIsNotNone(food, "Food entity should exist")
        
        # Check Human entity details
        self.assertEqual("A bipedal primate capable of complex thought.", human["description"])
        self.assertEqual("Species", human["type"])
        
        # Check Human attributes
        self.assertEqual(3, len(human["attributes"]))
        height_attr = next((a for a in human["attributes"] if a["name"] == "Average Height"), None)
        self.assertIsNotNone(height_attr)
        self.assertEqual("1.7 meters", height_attr["value"])
        self.assertIsNone(height_attr["url"])
        
        cognitive_attr = next((a for a in human["attributes"] if a["name"] == "Cognitive Ability"), None)
        self.assertIsNotNone(cognitive_attr)
        self.assertEqual("High", cognitive_attr["value"])
        self.assertEqual("/docs/cognition", cognitive_attr["url"])
        
        # Check Human relationships
        self.assertEqual(4, len(human["relationships"]))
        has_part_rel = next((r for r in human["relationships"] if r["type"] == "has_part"), None)
        self.assertIsNotNone(has_part_rel)
        self.assertEqual("Brain", has_part_rel["target"])
        
        # Check Brain entity
        self.assertEqual("The central organ of the nervous system.", brain["description"])
        self.assertEqual("Organ", brain["type"])
        self.assertEqual(0, len(brain["attributes"]))
        self.assertEqual(1, len(brain["relationships"]))
        
        # Check Apple entity
        self.assertEqual("A type of fruit, typically red or green.", apple["description"])
        self.assertEqual("Food", apple["type"])
        self.assertEqual(2, len(apple["attributes"]))
        
        nutritional_attr = next((a for a in apple["attributes"] if a["name"] == "Nutritional Info"), None)
        self.assertIsNotNone(nutritional_attr)
        self.assertEqual("Rich in vitamins", nutritional_attr["value"])
        self.assertEqual("/nutrition/apple", nutritional_attr["url"])

    def test_extract_entities_and_relationships(self):
        """Test extracting entities and relationships from the parsed structure."""
        parsed = parse_markdown_ontology(self.sample_markdown)
        entities, relationships = extract_entities_and_relationships(parsed)
        expected_entity_names = {"Human", "Brain", "Mammal", "Apple", "Food"}
        self.assertEqual(set(entities.keys()), expected_entity_names)
        
        expected_relationships = [
            {"source": "Human", "target": "Brain", "type": "has_part"}, 
            {"source": "Human", "target": "Mammal", "type": "member_of"}, 
            {"source": "Human", "target": "Apple", "type": "eats"}, 
            {"source": "Human", "target": "Food", "type": "eats"}, 
            {"source": "Brain", "target": "Human", "type": "part_of"}, 
            {"source": "Apple", "target": "Human", "type": "eaten_by"}
        ]
        
        self.assertCountEqual(relationships, expected_relationships)

    def test_convert_to_knowledge_graph(self):
        """Test converting structured ontology to knowledge graph."""
        parsed = parse_markdown_ontology(self.sample_markdown)
        knowledge_graph = convert_to_knowledge_graph(parsed)
        
        self.assertIn("nodes", knowledge_graph)
        self.assertIn("edges", knowledge_graph)
        
        # There should be 6 nodes (5 entities + 1 section node, as 'food' is both a section and entity)
        self.assertEqual(6, len(knowledge_graph["nodes"]), "Should have 6 nodes including section nodes")
        
        # Check node IDs
        node_ids = {node["id"] for node in knowledge_graph["nodes"]}
        
        # The 'food' ID is shared between the section and entity 
        expected_ids = {"human", "brain", "mammal", "apple", "food", "biology"}
        self.assertEqual(expected_ids, node_ids)
        
        human_node = next((node for node in knowledge_graph["nodes"] if node["id"] == "human"), None)
        apple_node = next((node for node in knowledge_graph["nodes"] if node["id"] == "apple"), None)
        
        self.assertIsNotNone(human_node)
        self.assertIsNotNone(apple_node)
        
        # Check attribute values match
        self.assertEqual("1.7 meters", human_node.get("average_height"))
        self.assertEqual("/docs/cognition", human_node.get("cognitive_ability_url"))
        self.assertEqual("Rich in vitamins", apple_node.get("nutritional_info"))
        self.assertEqual("/nutrition/apple", apple_node.get("nutritional_info_url"))
        
        # There should be 6 edges
        self.assertEqual(6, len(knowledge_graph["edges"]))
        
        expected_edges = [
            {"source": "human", "target": "brain", "label": "has_part"}, 
            {"source": "human", "target": "mammal", "label": "member_of"}, 
            {"source": "human", "target": "apple", "label": "eats"}, 
            {"source": "human", "target": "food", "label": "eats"}, 
            {"source": "brain", "target": "human", "label": "part_of"}, 
            {"source": "apple", "target": "human", "label": "eaten_by"}
        ]
        
        # Convert to a comparable format for set comparison
        actual_edge_set = {(e["source"], e["target"], e["label"]) for e in knowledge_graph["edges"]}
        expected_edge_set = {(e["source"], e["target"], e["label"]) for e in expected_edges}
        
        self.assertEqual(expected_edge_set, actual_edge_set)

    def test_extract_markdown_to_json(self):
        """Test end-to-end conversion from NEW markdown format to JSON."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".md") as temp_input:
            temp_input.write(self.sample_markdown)
            temp_input_path = temp_input.name
            
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".json") as temp_output:
            temp_output_path = temp_output.name
            
        try:
            extract_markdown_to_json(temp_input_path, temp_output_path)
            
            with open(temp_output_path, 'r') as f:
                result = json.load(f)
                
            self.assertIn("structured_ontology", result)
            self.assertIn("knowledge_graph", result)
            
            structured_ontology = result["structured_ontology"]
            self.assertIn("biology", structured_ontology)
            self.assertIn("food", structured_ontology)
            
            biology_entities = structured_ontology.get("biology", {}).get("entities", [])
            food_entities = structured_ontology.get("food", {}).get("entities", [])
            
            human_entity = next((entity for entity in biology_entities if entity.get("name") == "Human"), None)
            apple_entity = next((entity for entity in food_entities if entity.get("name") == "Apple"), None)
            
            self.assertIsNotNone(human_entity)
            self.assertEqual("Species", human_entity.get("type"))
            
            human_attrs = human_entity.get("attributes", [])
            cog_ability_attr = next((attr for attr in human_attrs if attr.get("name") == "Cognitive Ability"), None)
            
            self.assertIsNotNone(cog_ability_attr)
            self.assertEqual("High", cog_ability_attr.get("value"))
            self.assertEqual("/docs/cognition", cog_ability_attr.get("url"))
            
            knowledge_graph = result["knowledge_graph"]
            self.assertIn("nodes", knowledge_graph)
            self.assertIn("edges", knowledge_graph)
            
            node_ids = {node.get("id") for node in knowledge_graph.get("nodes", [])}
            self.assertIn("human", node_ids)
            self.assertIn("apple", node_ids)
            
            human_node_from_json = next((node for node in knowledge_graph.get("nodes", []) if node.get("id") == "human"), None)
            self.assertIsNotNone(human_node_from_json)
            self.assertEqual("1.7 meters", human_node_from_json.get("average_height"))
            self.assertEqual("/docs/cognition", human_node_from_json.get("cognitive_ability_url"))
            
        finally:
            os.unlink(temp_input_path)
            os.unlink(temp_output_path)

    def test_malformed_markdown(self):
        """Test handling of malformed markdown input."""
        # The real parser is more lenient than the mock, so only test truly invalid cases
        
        # Empty input
        empty_markdown = ""
        result = parse_markdown_ontology(empty_markdown)
        self.assertEqual({}, result)
        
        # Orphaned entity (no section header)
        orphaned_entity = "\n- Entity: Orphan\n  Description: Lost\n"
        result = parse_markdown_ontology(orphaned_entity)
        self.assertEqual({}, result)  # Should produce empty result

    def test_empty_input(self):
        """Test handling of empty input."""
        empty_markdown = ""
        result = parse_markdown_ontology(empty_markdown)
        self.assertEqual({}, result)

    def test_id_generation(self):
        """Test that IDs are properly generated from Entity names."""
        # Test make_id directly
        self.assertEqual("test_name", make_id("Test Name"))
        self.assertEqual("test_name", make_id("Test-Name"))
        self.assertEqual("test123", make_id("Test123"))
        
        # Test IDs in knowledge graph
        parsed = parse_markdown_ontology(self.sample_markdown)
        kg = convert_to_knowledge_graph(parsed)
        
        node_ids = {node["id"] for node in kg["nodes"]}
        edge_sources = {edge["source"] for edge in kg["edges"]}
        edge_targets = {edge["target"] for edge in kg["edges"]}
        
        expected_ids = {"human", "brain", "mammal", "apple", "food", "biology"}
        self.assertEqual(expected_ids, node_ids)
        self.assertTrue(edge_sources.issubset(node_ids))
        self.assertTrue(edge_targets.issubset(node_ids))

    def test_entity_type_extraction(self):
        """Test proper extraction of entity types."""
        parsed = parse_markdown_ontology(self.sample_markdown)
        entities, _ = extract_entities_and_relationships(parsed)
        
        self.assertEqual("Species", entities["Human"]["type"])
        self.assertEqual("Organ", entities["Brain"]["type"])
        self.assertEqual("Class", entities["Mammal"]["type"])
        self.assertEqual("Food", entities["Apple"]["type"])
        self.assertEqual("Concept", entities["Food"]["type"])

    def test_attribute_with_url_parsing(self):
        """Test specifically that attributes with URLs are parsed correctly."""
        parsed = parse_markdown_ontology(self.sample_markdown)
        human_entity = next((entity for entity in parsed.get("biology", {}).get("entities", []) if entity.get("name") == "Human"), None)
        apple_entity = next((entity for entity in parsed.get("food", {}).get("entities", []) if entity.get("name") == "Apple"), None)
        
        self.assertIsNotNone(human_entity)
        self.assertIsNotNone(apple_entity)
        
        cognitive_attr = next((attr for attr in human_entity.get("attributes", []) if attr.get("name") == "Cognitive Ability"), None)
        nutritional_attr = next((attr for attr in apple_entity.get("attributes", []) if attr.get("name") == "Nutritional Info"), None)
        
        self.assertIsNotNone(cognitive_attr)
        self.assertEqual("High", cognitive_attr.get("value"))
        self.assertEqual("/docs/cognition", cognitive_attr.get("url"))
        
        self.assertIsNotNone(nutritional_attr)
        self.assertEqual("Rich in vitamins", nutritional_attr.get("value"))
        self.assertEqual("/nutrition/apple", nutritional_attr.get("url"))

    def test_attribute_without_url_parsing(self):
        """Test specifically that attributes without URLs are parsed correctly."""
        parsed = parse_markdown_ontology(self.sample_markdown)
        human_entity = next((entity for entity in parsed.get("biology", {}).get("entities", []) if entity.get("name") == "Human"), None)
        apple_entity = next((entity for entity in parsed.get("food", {}).get("entities", []) if entity.get("name") == "Apple"), None)
        
        self.assertIsNotNone(human_entity)
        self.assertIsNotNone(apple_entity)
        
        height_attr = next((attr for attr in human_entity.get("attributes", []) if attr.get("name") == "Average Height"), None)
        color_attr = next((attr for attr in apple_entity.get("attributes", []) if attr.get("name") == "Color"), None)
        
        self.assertIsNotNone(height_attr)
        self.assertEqual("1.7 meters", height_attr.get("value"))
        self.assertIsNone(height_attr.get("url"))
        
        self.assertIsNotNone(color_attr)
        self.assertEqual("Red/Green", color_attr.get("value"))
        self.assertIsNone(color_attr.get("url"))