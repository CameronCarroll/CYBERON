import re
import json
from typing import Dict, List, Set, Tuple, Any, Optional
import unittest
import tempfile
import os

# --- generate_id, other mocks remain the same ---
def generate_id(name: Optional[str]) -> str:
    """Generates a standardized ID from a name string."""
    if name is None: return "unknown_id"
    s = name.lower()
    s = re.sub(r'[^a-z0-9]+', '_', s)
    s = s.strip('_')
    if not s: return "invalid_id"
    return s

def parse_markdown_ontology(markdown_text: str) -> Dict:
    """
    (Mock Revised Again) Parses markdown ontology in the NEW format.
    Handles whitespace variations in list items, comments in Target, and corrects logic flow.
    """
    if not markdown_text.strip():
        return {}

    lines = markdown_text.strip().split('\n')
    ontology = {}
    current_section = None
    current_entity_data = None
    in_attributes = False
    in_relationships = False

    for line_num, line_raw in enumerate(lines):
        line = line_raw.strip()
        if not line:
            continue

        # --- Top Level Elements ---
        if line.startswith('# '):
            current_section = line[2:].strip()
            if not current_section: raise ValueError(f"Line {line_num+1}: Main section heading '#' cannot be empty.")
            ontology[current_section] = {"entities": {}}
            current_entity_data = None
            in_attributes = False
            in_relationships = False
            continue

        if line.startswith('## '):
            in_attributes = False
            in_relationships = False
            continue

        # --- List Items (Entity, Attribute, Relationship) ---
        if line.startswith('-'):
            content = line[1:].lstrip()

            if content.startswith('Entity:'):
                if not current_section: raise ValueError(f"Line {line_num+1}: Entity definition found before any section '#'.")
                entity_name = content.split(':', 1)[1].strip()
                if not entity_name: raise ValueError(f"Line {line_num+1}: '- Entity:' must have a name.")
                current_entity_data = { "name": entity_name, "description": None, "type": None, "attributes": [], "relationships": [] }
                ontology[current_section]["entities"][entity_name] = current_entity_data
                in_attributes = False
                in_relationships = False
                continue

            elif content.startswith('Attribute:'):
                if not current_entity_data: raise ValueError(f"Line {line_num+1}: Found '- Attribute:' outside of a defined Entity context.")
                if not in_attributes: raise ValueError(f"Line {line_num+1}: Found '- Attribute:' before 'Attributes:' section or after non-attribute property.")
                full_attr_text = content.split(':', 1)[1].strip()
                if not full_attr_text: raise ValueError(f"Line {line_num+1}: '- Attribute:' must have a name.")
                url_match = re.search(r'\s*\[url:(.*?)\]$', full_attr_text)
                attr_data = {}
                if url_match:
                    attr_name = full_attr_text[:url_match.start()].strip()
                    url = url_match.group(1).strip()
                    if not attr_name: raise ValueError(f"Line {line_num+1}: Attribute name cannot be empty before URL part.")
                    attr_data = {"name": attr_name, "value": None, "external_url": url}
                else:
                    attr_data = {"name": full_attr_text, "value": None}
                current_entity_data["attributes"].append(attr_data)
                continue

            elif content.startswith('Relationship:'):
                 if not current_entity_data: raise ValueError(f"Line {line_num+1}: Found '- Relationship:' outside of a defined Entity context.")
                 if not in_relationships: raise ValueError(f"Line {line_num+1}: Found '- Relationship:' before 'Relationships:' section.")
                 rel_type = content.split(':', 1)[1].strip()
                 if not rel_type: raise ValueError(f"Line {line_num+1}: '- Relationship:' must have a type.")
                 current_entity_data["relationships"].append({"type": rel_type, "target": None})
                 continue
            else:
                 raise ValueError(f"Line {line_num+1}: Unknown or invalid list item format: '{line}'")

        # --- Entity Properties (Description, Type, Value, Target, etc.) ---
        if current_entity_data:
            if line.startswith('Description:'):
                current_entity_data["description"] = line.split(':', 1)[1].strip()
                in_attributes = False
                in_relationships = False
                continue

            elif line.startswith('Type:'):
                current_entity_data["type"] = line.split(':', 1)[1].strip()
                in_attributes = False
                in_relationships = False
                continue

            elif line.startswith('Attributes:'):
                in_attributes = True
                in_relationships = False
                continue

            elif line.startswith('Relationships:'):
                in_attributes = False
                in_relationships = True
                continue

            elif line.startswith('Value:'):
                if not in_attributes or not current_entity_data["attributes"]:
                     raise ValueError(f"Line {line_num+1}: Found 'Value:' without a preceding '- Attribute:' needing a value in the current Attributes block.")
                attr_value = line.split(':', 1)[1].strip()
                attr_to_update = None
                for i in range(len(current_entity_data["attributes"]) - 1, -1, -1):
                    if current_entity_data["attributes"][i]["value"] is None:
                        attr_to_update = current_entity_data["attributes"][i]
                        break
                if attr_to_update is None: raise ValueError(f"Line {line_num+1}: Found 'Value:' but no preceding '- Attribute:' is awaiting a value.")
                attr_to_update["value"] = attr_value
                continue

            elif line.startswith('Target:'):
                if not in_relationships or not current_entity_data["relationships"] or current_entity_data["relationships"][-1]["target"] is not None:
                     raise ValueError(f"Line {line_num+1}: Found 'Target:' without a preceding '- Relationship:' needing a target in the current Relationships block.")

                # --- Correction: Remove inline comments ---
                target_full_string = line.split(':', 1)[1]
                target_name = target_full_string.split('#', 1)[0].strip() # Split at #, take first part, strip whitespace
                # --- End Correction ---

                if not target_name: raise ValueError(f"Line {line_num+1}: 'Target:' must have a name (after removing comments).")
                current_entity_data["relationships"][-1]["target"] = target_name
                continue

        # --- Invalid lines outside known contexts ---
        if line.startswith(('Description:', 'Type:', 'Attributes:', 'Relationships:', 'Value:', 'Target:')):
             raise ValueError(f"Line {line_num+1}: Ontology property '{line.split(':')[0]}' found outside a defined Entity context.")
        else:
             raise ValueError(f"Line {line_num+1}: Unrecognized or misplaced line: '{line}'")

    if not ontology and markdown_text.strip():
         if not any(l.strip().startswith('# ') for l in lines):
              raise ValueError("Markdown does not start with a top-level heading '# '")
    return ontology

# --- Other mocks (extract_entities_and_relationships, convert_to_knowledge_graph, extract_markdown_to_json) remain the same ---
def extract_entities_and_relationships(parsed_ontology):
     entities = {}
     relationships = []
     for section_data in parsed_ontology.values():
         for entity_name, entity_data in section_data.get("entities", {}).items():
             entities[entity_name] = {"type": entity_data.get("type"), "description": entity_data.get("description")}
             for rel in entity_data.get("relationships", []):
                 if rel.get("target") and rel.get("type"):
                      relationships.append({"source": entity_name, "target": rel["target"], "type": rel["type"]})
     return entities, relationships

def convert_to_knowledge_graph(parsed_ontology):
    nodes = []
    edges = []
    added_nodes = set()
    for section_name, section_data in parsed_ontology.items():
        for entity_name, entity_data in section_data.get("entities", {}).items():
            entity_id = generate_id(entity_name)
            if entity_id not in added_nodes:
                node_data = {"id": entity_id, "label": entity_name, "type": entity_data.get("type", "Unknown"), "description": entity_data.get("description")}
                for attr in entity_data.get("attributes", []):
                    if attr.get("name"):
                        attr_id = generate_id(attr["name"])
                        node_data[attr_id] = attr.get("value")
                        if "external_url" in attr: node_data[f"{attr_id}_url"] = attr["external_url"]
                nodes.append(node_data)
                added_nodes.add(entity_id)
            for rel in entity_data.get("relationships", []):
                 if rel.get("target") and rel.get("type"):
                     source_id = entity_id
                     target_id = generate_id(rel["target"])
                     edges.append({"source": source_id, "target": target_id, "label": rel["type"]})
    edge_target_ids = {edge['target'] for edge in edges}
    existing_node_ids = {node['id'] for node in nodes}
    missing_target_ids = edge_target_ids - existing_node_ids
    for missing_id in missing_target_ids:
        nodes.append({"id": missing_id, "label": missing_id.replace('_', ' ').title(), "type": "Unknown"})
        added_nodes.add(missing_id)
    return {"nodes": nodes, "edges": edges}

def extract_markdown_to_json(input_path, output_path):
     with open(input_path, 'r') as infile: markdown_content = infile.read()
     structured_ontology = parse_markdown_ontology(markdown_content)
     knowledge_graph = convert_to_knowledge_graph(structured_ontology)
     output_data = {"structured_ontology": structured_ontology, "knowledge_graph": knowledge_graph}
     with open(output_path, 'w') as outfile: json.dump(output_data, outfile, indent=4)


# --- Test Class ---
class TestNewMarkdownOntologyParser(unittest.TestCase):
    # --- setUp remains the same ---
    def setUp(self):
        """Set up test fixtures with the NEW format."""
        self.sample_markdown = """
# Biology

## Organisms

-   Entity: Human
    Description: A bipedal primate capable of complex thought.
    Type: Species
    Attributes:
        -   Attribute: Average Height
            Value: 1.7 meters
        -   Attribute: Lifespan
            Value: 80 years
        -   Attribute: Cognitive Ability [url:/docs/cognition]
            Value: High
    Relationships:
        -   Relationship: has_part
            Target: Brain
        -   Relationship: member_of
            Target: Mammal
        -   Relationship: eats
            Target: Apple
        -   Relationship: eats
            Target: Food # Generic Food relationship

-   Entity: Brain
    Description: The central organ of the nervous system.
    Type: Organ
    Relationships:
        -   Relationship: part_of
            Target: Human

-   Entity: Mammal
    Description: A class of warm-blooded vertebrates.
    Type: Class


## Food

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
        self.expected_structure = { # Expected structure matches the target now
            "Biology": {
                "entities": {
                    "Human": {
                        "name": "Human", "description": "A bipedal primate capable of complex thought.", "type": "Species",
                        "attributes": [{"name": "Average Height", "value": "1.7 meters"}, {"name": "Lifespan", "value": "80 years"}, {"name": "Cognitive Ability", "value": "High", "external_url": "/docs/cognition"}],
                        "relationships": [{"type": "has_part", "target": "Brain"}, {"type": "member_of", "target": "Mammal"}, {"type": "eats", "target": "Apple"}, {"type": "eats", "target": "Food"}] # Corrected 'Food' target
                    },
                    "Brain": {"name": "Brain", "description": "The central organ of the nervous system.", "type": "Organ", "attributes": [], "relationships": [{"type": "part_of", "target": "Human"}]},
                    "Mammal": {"name": "Mammal", "description": "A class of warm-blooded vertebrates.", "type": "Class", "attributes": [], "relationships": []},
                    "Apple": {"name": "Apple", "description": "A type of fruit, typically red or green.", "type": "Food", "attributes": [{"name": "Color", "value": "Red/Green"}, {"name": "Nutritional Info", "value": "Rich in vitamins", "external_url": "/nutrition/apple"}], "relationships": [{"type": "eaten_by", "target": "Human"}]},
                    "Food": {"name": "Food", "description": "Any substance consumed to provide nutritional support.", "type": "Concept", "attributes": [], "relationships": []}
                }}}
        self.expected_node_ids = {"human", "brain", "mammal", "apple", "food"}
        self.expected_human_attr_keys = {"average_height", "lifespan", "cognitive_ability", "cognitive_ability_url"}
        self.expected_apple_attr_keys = {"color", "nutritional_info", "nutritional_info_url"}

    # --- Other test methods remain the same ---
    def test_parse_markdown_ontology(self):
        """Test parsing NEW markdown format into structured ontology."""
        result = parse_markdown_ontology(self.sample_markdown)
        self.maxDiff = None
        self.assertEqual(result, self.expected_structure) # Should pass now

    def test_extract_entities_and_relationships(self):
        """Test extracting entities and relationships from the NEW structure."""
        entities, relationships = extract_entities_and_relationships(self.expected_structure)
        expected_entity_names = {"Human", "Brain", "Mammal", "Apple", "Food"}
        self.assertEqual(set(entities.keys()), expected_entity_names)
        expected_relationships = [{"source": "Human", "target": "Brain", "type": "has_part"}, {"source": "Human", "target": "Mammal", "type": "member_of"}, {"source": "Human", "target": "Apple", "type": "eats"}, {"source": "Human", "target": "Food", "type": "eats"}, {"source": "Brain", "target": "Human", "type": "part_of"}, {"source": "Apple", "target": "Human", "type": "eaten_by"}]
        self.assertCountEqual(relationships, expected_relationships)

    def test_convert_to_knowledge_graph(self):
        """Test converting NEW structured ontology to knowledge graph."""
        knowledge_graph = convert_to_knowledge_graph(self.expected_structure)
        self.assertIn("nodes", knowledge_graph); self.assertIn("edges", knowledge_graph)
        self.assertEqual(len(knowledge_graph["nodes"]), 5)
        node_ids = {node["id"] for node in knowledge_graph["nodes"]}
        self.assertEqual(node_ids, self.expected_node_ids)
        human_node = next((node for node in knowledge_graph["nodes"] if node["id"] == "human"), None)
        apple_node = next((node for node in knowledge_graph["nodes"] if node["id"] == "apple"), None)
        self.assertIsNotNone(human_node); self.assertIsNotNone(apple_node)
        self.assertEqual(human_node.get("average_height"), "1.7 meters")
        self.assertEqual(human_node.get("cognitive_ability_url"), "/docs/cognition")
        self.assertEqual(apple_node.get("nutritional_info"), "Rich in vitamins")
        self.assertEqual(apple_node.get("nutritional_info_url"), "/nutrition/apple")
        self.assertEqual(len(knowledge_graph["edges"]), 6)
        expected_edges = [{"source": "human", "target": "brain", "label": "has_part"}, {"source": "human", "target": "mammal", "label": "member_of"}, {"source": "human", "target": "apple", "label": "eats"}, {"source": "human", "target": "food", "label": "eats"}, {"source": "brain", "target": "human", "label": "part_of"}, {"source": "apple", "target": "human", "label": "eaten_by"}]
        actual_edge_set = set(tuple(sorted(edge.items())) for edge in knowledge_graph["edges"])
        expected_edge_set = set(tuple(sorted(edge.items())) for edge in expected_edges)
        self.assertEqual(actual_edge_set, expected_edge_set)

    def test_extract_markdown_to_json(self):
        """Test end-to-end conversion from NEW markdown format to JSON."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".md") as temp_input: temp_input.write(self.sample_markdown); temp_input_path = temp_input.name
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".json") as temp_output: temp_output_path = temp_output.name
        try:
            extract_markdown_to_json(temp_input_path, temp_output_path)
            with open(temp_output_path, 'r') as f: result = json.load(f)
            self.assertIn("structured_ontology", result); self.assertIn("knowledge_graph", result)
            structured_ontology = result["structured_ontology"]
            self.assertIn("Biology", structured_ontology)
            biology_entities = structured_ontology.get("Biology", {}).get("entities", {})
            self.assertIn("Human", biology_entities); self.assertIn("Apple", biology_entities)
            human_entity = biology_entities.get("Human", {})
            self.assertEqual(human_entity.get("type"), "Species")
            human_attrs = human_entity.get("attributes", [])
            cog_ability_attr = next((attr for attr in human_attrs if attr.get("name") == "Cognitive Ability"), None)
            self.assertIsNotNone(cog_ability_attr); self.assertEqual(cog_ability_attr.get("value"), "High"); self.assertEqual(cog_ability_attr.get("external_url"), "/docs/cognition")
            knowledge_graph = result["knowledge_graph"]
            self.assertIn("nodes", knowledge_graph); self.assertIn("edges", knowledge_graph)
            node_ids = {node.get("id") for node in knowledge_graph.get("nodes", [])}
            self.assertIn("human", node_ids); self.assertIn("apple", node_ids)
            human_node_from_json = next((node for node in knowledge_graph.get("nodes", []) if node.get("id") == "human"), None)
            self.assertIsNotNone(human_node_from_json); self.assertEqual(human_node_from_json.get("average_height"), "1.7 meters"); self.assertEqual(human_node_from_json.get("cognitive_ability_url"), "/docs/cognition")
        finally:
            os.unlink(temp_input_path); os.unlink(temp_output_path)

    def test_malformed_markdown(self):
        """Test handling of malformed markdown input in the NEW format."""
        malformed1 = "\n# Biology\n- Entity:\n  Description: Something\n"
        malformed2 = "\n# Biology\n- Entity: Human\n  Attributes:\n    Value: 1.7 meters\n" # Value before - Attribute:
        malformed3 = "\n# Biology\n- Entity: Human\n  Relationships:\n    Target: Brain\n" # Target before - Relationship:
        malformed4 = "\n- Entity: Orphan\n  Description: Lost\n" # Entity before # Section
        malformed5 = "\n# Section\n- Entity: Test\n  - Attribute: Name [url:/path]\n    Value: TestValue\n" # Attribute outside Attributes:
        malformed6 = "\n# Section\n- Entity: Test\n  Attributes:\n  Value: BadValuePlacement\n" # Value inside Attributes: but before - Attribute:
        malformed7 = "\n# Section\n- Entity: Test\n  Attributes:\n  - Attribute:\n    Value: EmptyAttrName\n" # Empty - Attribute: name

        with self.assertRaisesRegex(ValueError, r"Line \d+: '- Entity:' must have a name", msg="Parser should fail on missing entity name"):
             parse_markdown_ontology(malformed1)
        # Check Value without preceding '- Attribute:' (even outside 'Attributes:' block)
        with self.assertRaisesRegex(ValueError, r"Line \d+: Found 'Value:' without a preceding '- Attribute:' needing a value", msg="Parser should fail on Value without preceding Attribute"):
             parse_markdown_ontology(malformed2)
        # Check Target without preceding '- Relationship:' (even outside 'Relationships:' block)
        with self.assertRaisesRegex(ValueError, r"Line \d+: Found 'Target:' without a preceding '- Relationship:' needing a target", msg="Parser should fail on Target without preceding Relationship"):
             parse_markdown_ontology(malformed3)
        # Check Entity before Section
        with self.assertRaisesRegex(ValueError, r"Line \d+: Entity definition found before any section '#'", msg="Parser should fail on entity outside section"):
            parse_markdown_ontology(malformed4)
        # Check '- Attribute:' outside 'Attributes:' block
        with self.assertRaisesRegex(ValueError, r"Line \d+: Found '- Attribute:' before 'Attributes:' section or after non-attribute property.", msg="Attribute should require Attributes section"):
             parse_markdown_ontology(malformed5)

        # --- THIS IS THE CORRECTED ASSERTION FOR malformed6 ---
        # Check 'Value:' inside 'Attributes:' block but before any '- Attribute:'
        with self.assertRaisesRegex(ValueError, r"Line \d+: Found 'Value:' without a preceding '- Attribute:' needing a value", msg="Parser should fail on misplaced Value inside Attributes block"):
             parse_markdown_ontology(malformed6)
        # --- END CORRECTION ---

        # Check empty '- Attribute:' name
        with self.assertRaisesRegex(ValueError, r"Line \d+: '- Attribute:' must have a name", msg="Parser should fail on empty Attribute name"):
             parse_markdown_ontology(malformed7)

    # --- Other test methods remain unchanged ---
    def test_empty_input(self):
        """Test handling of empty input."""
        empty_markdown = ""
        result = parse_markdown_ontology(empty_markdown)
        self.assertEqual(result, {})

    def test_id_generation(self):
        """Test that IDs are properly generated from Entity names."""
        kg = convert_to_knowledge_graph(self.expected_structure)
        node_ids = {node["id"] for node in kg["nodes"]}
        edge_sources = {edge["source"] for edge in kg["edges"]}
        edge_targets = {edge["target"] for edge in kg["edges"]}
        self.assertEqual(node_ids, self.expected_node_ids)
        self.assertTrue(edge_sources.issubset(node_ids))
        self.assertTrue(edge_targets.issubset(node_ids))

    def test_entity_type_extraction(self):
        """Test proper extraction of entity types."""
        entities, _ = extract_entities_and_relationships(self.expected_structure)
        self.assertEqual(entities["Human"]["type"], "Species"); self.assertEqual(entities["Brain"]["type"], "Organ") # etc.

    def test_attribute_with_url_parsing(self):
         """Test specifically that attributes with URLs are parsed correctly."""
         parsed = parse_markdown_ontology(self.sample_markdown)
         human_attributes = parsed.get("Biology", {}).get("entities", {}).get("Human", {}).get("attributes", [])
         apple_attributes = parsed.get("Biology", {}).get("entities", {}).get("Apple", {}).get("attributes", [])
         cognitive_attr = next((attr for attr in human_attributes if attr.get("name") == "Cognitive Ability"), None)
         nutritional_attr = next((attr for attr in apple_attributes if attr.get("name") == "Nutritional Info"), None)
         self.assertIsNotNone(cognitive_attr); self.assertEqual(cognitive_attr.get("value"), "High"); self.assertIn("external_url", cognitive_attr); self.assertEqual(cognitive_attr.get("external_url"), "/docs/cognition")
         self.assertIsNotNone(nutritional_attr); self.assertEqual(nutritional_attr.get("value"), "Rich in vitamins"); self.assertIn("external_url", nutritional_attr); self.assertEqual(nutritional_attr.get("external_url"), "/nutrition/apple")

    def test_attribute_without_url_parsing(self):
         """Test specifically that attributes without URLs are parsed correctly."""
         parsed = parse_markdown_ontology(self.sample_markdown)
         human_attributes = parsed.get("Biology", {}).get("entities", {}).get("Human", {}).get("attributes", [])
         apple_attributes = parsed.get("Biology", {}).get("entities", {}).get("Apple", {}).get("attributes", [])
         height_attr = next((attr for attr in human_attributes if attr.get("name") == "Average Height"), None)
         color_attr = next((attr for attr in apple_attributes if attr.get("name") == "Color"), None)
         self.assertIsNotNone(height_attr); self.assertEqual(height_attr.get("value"), "1.7 meters"); self.assertNotIn("external_url", height_attr)
         self.assertIsNotNone(color_attr); self.assertEqual(color_attr.get("value"), "Red/Green"); self.assertNotIn("external_url", color_attr)

# if __name__ == '__main__':
#      unittest.main()