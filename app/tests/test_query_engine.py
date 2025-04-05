import unittest
import pytest
import networkx as nx
import json
import uuid
import re
import copy
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, mock_open, MagicMock

# Module under test
from app.models.query_engine import CyberneticsQueryEngine



# --- Enhanced Sample Data ---
# Use a fixed base time for predictable timestamps
BASE_TIME_STR = "2025-04-05T10:00:00Z"
BASE_TIME = datetime.fromisoformat(BASE_TIME_STR.replace("Z", "+00:00"))

SAMPLE_DATA = {
    "structured_ontology": {
        "1": {
            "title": "Core Cybernetics Principles",
            "subsections": {
                "Feedback Loops": ["Positive Feedback", "Negative Feedback", "Homeostasis"],
                "Control Theory": ["PID Controllers", "State-Space Representation"]
            }
        },
        "2": {
            "title": "Applications",
            "subsections": {
                "Robotics": ["Sensor Fusion", "Motion Planning"],
                "Biology": ["Regulation Systems", "Ecosystem Dynamics (simple)"]
            }
        }
    },
    "knowledge_graph": {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"id": "feedback", "label": "Feedback", "type": "concept", "created_at": (BASE_TIME - timedelta(days=2)).isoformat() + "Z", "description": "Core concept of feedback."},
            {"id": "control_theory", "label": "Control Theory", "type": "theory", "created_at": (BASE_TIME - timedelta(days=1)).isoformat() + "Z"},
            {"id": "homeostasis", "label": "Homeostasis", "type": "concept", "created_at": BASE_TIME.isoformat() + "Z", "description": "Maintaining stability."},
            {"id": "robotics", "label": "Robotics", "type": "application", "created_at": (BASE_TIME + timedelta(days=1)).isoformat() + "Z"},
             {"id": "ai", "label": "Artificial Intelligence", "type": "field", "created_at": (BASE_TIME - timedelta(days=3)).isoformat() + "Z"}
        ],
        "edges": [
            {"id": str(uuid.uuid4()), "source": "feedback", "target": "control_theory", "label": "is_central_to", "created_at": (BASE_TIME - timedelta(hours=10)).isoformat() + "Z"},
            {"id": str(uuid.uuid4()), "source": "feedback", "target": "homeostasis", "label": "enables", "created_at": (BASE_TIME - timedelta(hours=5)).isoformat() + "Z"},
            {"id": str(uuid.uuid4()), "source": "control_theory", "target": "robotics", "label": "applied_in", "created_at": BASE_TIME.isoformat() + "Z"},
             {"id": str(uuid.uuid4()), "source": "ai", "target": "robotics", "label": "related_to", "created_at": (BASE_TIME + timedelta(hours=2)).isoformat() + "Z"}
        ]
    }
}

class TestCyberneticsQueryEngineComprehensive(unittest.TestCase):
    """Comprehensive tests for the CyberneticsQueryEngine class"""

    def setUp(self):
        """Set up test environment for each test"""
        # Use deepcopy to prevent tests from interfering with each other's data
        self.sample_data_copy = copy.deepcopy(SAMPLE_DATA)
        mock_data_json = json.dumps(self.sample_data_copy)

        # Mock file open to return our sample data
        m = mock_open(read_data=mock_data_json)
        with patch("builtins.open", m):
            self.engine = CyberneticsQueryEngine("fake_path.json") # Path doesn't matter due to mock

        # --- Verification after load ---
        self.assertIsInstance(self.engine.graph, nx.DiGraph)
        self.assertTrue(self.engine.graph.is_directed())
        self.assertFalse(self.engine.graph.is_multigraph())
        self.assertEqual(len(self.engine.graph.nodes), 5) # Updated count
        self.assertEqual(len(self.engine.graph.edges), 4) # Updated count

    # --- Core Querying Tests (Keep existing good tests) ---
    def test_query_entity_success(self):
        result = self.engine.query_entity("feedback")
        self.assertEqual(result["id"], "feedback")
        self.assertEqual(result["attributes"]["label"], "Feedback")
        self.assertEqual(result["attributes"]["type"], "concept")
        self.assertEqual(result["attributes"]["description"], "Core concept of feedback.")
        self.assertEqual(len(result["incoming"]), 0)
        self.assertEqual(len(result["outgoing"]), 2)
        outgoing_ids = {conn["id"] for conn in result["outgoing"]}
        self.assertIn("control_theory", outgoing_ids)
        self.assertIn("homeostasis", outgoing_ids)

    def test_query_entity_not_found(self):
        result = self.engine.query_entity("nonexistent")
        self.assertIn("error", result)

    def test_find_paths_success(self):
        paths = self.engine.find_paths("feedback", "robotics", max_length=3)
        self.assertGreater(len(paths), 0)
        first_path = paths[0]
        self.assertEqual(first_path[0]["id"], "feedback")
        self.assertEqual(first_path[-1]["id"], "robotics")
        self.assertIn("relationship_to_next", first_path[0]) # feedback -> control_theory
        self.assertEqual(first_path[0]["relationship_to_next"], "is_central_to")
        path_strings = ["->".join([n['id'] for n in p]) for p in paths]
        self.assertIn("feedback->control_theory->robotics", path_strings)

    def test_find_paths_no_path(self):
        paths = self.engine.find_paths("feedback", "ai", max_length=3) # No directed path
        self.assertEqual(len(paths), 0)

    def test_find_connections(self):
        connections = self.engine.find_connections("feedback", max_distance=2)
        self.assertIn(1, connections)
        self.assertEqual(len(connections[1]), 2) # control_theory, homeostasis
        distance_1_ids = {node["id"] for node in connections[1]}
        self.assertIn("control_theory", distance_1_ids)
        self.assertIn("homeostasis", distance_1_ids)

        self.assertIn(2, connections)
        self.assertEqual(len(connections[2]), 1) # robotics (via control_theory)
        self.assertEqual(connections[2][0]['id'], 'robotics')

    def test_search_entities(self):
        results = self.engine.search_entities("feedback")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "feedback")

        results = self.engine.search_entities("theory") # Partial match
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "control_theory")

        results = self.engine.search_entities("concept") # Match description
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "feedback")


        results = self.engine.search_entities("o", entity_types=["concept"])
        self.assertEqual(len(results), 2) # feedback, homeostasis
        result_ids = {r["id"] for r in results}
        self.assertIn("feedback", result_ids)
        self.assertIn("homeostasis", result_ids)

    # --- Analysis Tests (Keep/Expand) ---
    def test_get_central_entities(self):
        central = self.engine.get_central_entities(top_n=3)
        self.assertLessEqual(len(central), 3)
        # Expected degrees (in+out): feedback=2, control_theory=2, homeostasis=1, robotics=2, ai=1
        # Centrality (normalized by N-1=4): feedback=0.5, control_theory=0.5, homeostasis=0.25, robotics=0.5, ai=0.25
        # Top 3 should be feedback, control_theory, robotics
        central_ids = {e['id'] for e in central}
        self.assertIn("feedback", central_ids)
        self.assertIn("control_theory", central_ids)
        self.assertIn("robotics", central_ids)
        for entity in central:
            self.assertIn("centrality", entity)
            self.assertIn("connections", entity) # Total degree
            if entity['id'] == 'homeostasis': self.assertEqual(entity['connections'], 1)
            if entity['id'] == 'feedback': self.assertEqual(entity['connections'], 2)


    def test_get_related_concepts(self):
        related = self.engine.get_related_concepts("feedback")
        self.assertIn("is_central_to", related)
        self.assertEqual(related["is_central_to"][0]["id"], "control_theory")
        self.assertEqual(related["is_central_to"][0]["direction"], "outgoing")
        self.assertIn("enables", related)
        self.assertEqual(related["enables"][0]["id"], "homeostasis")
        self.assertEqual(related["enables"][0]["direction"], "outgoing")
        # Should not have incoming for feedback
        self.assertEqual(len(related), 2)


        related_robotics = self.engine.get_related_concepts("robotics")
        self.assertIn("inverse_applied_in", related_robotics)
        self.assertEqual(related_robotics["inverse_applied_in"][0]["id"], "control_theory")
        self.assertEqual(related_robotics["inverse_applied_in"][0]["direction"], "incoming")
        self.assertIn("inverse_related_to", related_robotics)
        self.assertEqual(related_robotics["inverse_related_to"][0]["id"], "ai")
        self.assertEqual(related_robotics["inverse_related_to"][0]["direction"], "incoming")
        self.assertEqual(len(related_robotics), 2) # No outgoing defined

        # Test filtering
        related_filtered = self.engine.get_related_concepts("feedback", relationship_types=["enables"])
        self.assertIn("enables", related_filtered)
        self.assertNotIn("is_central_to", related_filtered)
        self.assertEqual(len(related_filtered), 1)

    def test_get_entity_types(self):
        types = self.engine.get_entity_types()
        self.assertEqual(types.get("concept"), 2) # feedback, homeostasis
        self.assertEqual(types.get("theory"), 1)  # control_theory
        self.assertEqual(types.get("application"), 1) # robotics
        self.assertEqual(types.get("field"), 1) # ai
        self.assertEqual(len(types), 4)

    def test_get_relationship_types(self):
        rel_types = self.engine.get_relationship_types()
        self.assertEqual(rel_types.get("is_central_to"), 1)
        self.assertEqual(rel_types.get("enables"), 1)
        self.assertEqual(rel_types.get("applied_in"), 1)
        self.assertEqual(rel_types.get("related_to"), 1)
        self.assertEqual(len(rel_types), 4)

    def test_analyze_concept_hierarchy(self):
        # Add a simple hierarchy for testing
        self.engine.graph.add_node("root_concept", label="Root", type="root")
        self.engine.graph.add_edge("root_concept", "feedback", label="contains")
        self.engine.graph.add_edge("root_concept", "ai", label="contains")

        analysis = self.engine.analyze_concept_hierarchy()

        self.assertIn("root_nodes", analysis)
        self.assertEqual(len(analysis["root_nodes"]), 1)
        self.assertEqual(analysis["root_nodes"][0]["id"], "root_concept")
        # CORRECTED: BFS finds shortest paths, robotics is found at depth 2 via AI.
        self.assertEqual(analysis["root_nodes"][0]["max_depth"], 2)

        self.assertIn("hierarchies", analysis)
        self.assertIn("root_concept", analysis["hierarchies"])
        hierarchy = analysis["hierarchies"]["root_concept"]
        self.assertIn("0", hierarchy) # Depth 0
        self.assertEqual(hierarchy["0"][0]["id"], "root_concept")
        self.assertIn("1", hierarchy) # Depth 1
        depth1_ids = {n["id"] for n in hierarchy["1"]}
        self.assertIn("feedback", depth1_ids)
        self.assertIn("ai", depth1_ids)
        # Check depth 2 includes nodes reachable via shortest path length 2
        self.assertIn("2", hierarchy)
        depth2_ids = {n["id"] for n in hierarchy["2"]}
        self.assertIn("control_theory", depth2_ids) # via feedback
        self.assertIn("homeostasis", depth2_ids)    # via feedback
        self.assertIn("robotics", depth2_ids)       # via ai

        # Node 'robotics' via the feedback path would be depth 3, but BFS finds it at 2 first.
        # Therefore, max depth from root is 2.

    def test_get_concept_evolution(self):
         # Add evolution relationships
        evo_id = str(uuid.uuid4())
        # First remove existing edge to avoid duplicate edges
        for _, _, data in list(self.engine.graph.edges(data=True)):
            if data.get('label') == "is_central_to" and self.engine.graph.has_edge("feedback", "control_theory"):
                self.engine.graph.remove_edge("feedback", "control_theory")
                break
                
        # Add the evolved_into edge
        self.engine.graph.add_edge("feedback", "control_theory", id=evo_id, label="evolved_into")
        
        chains = self.engine.get_concept_evolution()
        self.assertEqual(len(chains), 1)
        chain = chains[0]
        self.assertEqual(len(chain), 2)
        self.assertEqual(chain[0]["id"], "feedback")
        self.assertEqual(chain[1]["id"], "control_theory")
        
        # Clean up - remove our evolution edge
        self.engine.graph.remove_edge("feedback", "control_theory")

    def test_generate_ontology_summary(self):
        summary = self.engine.generate_ontology_summary()
        self.assertEqual(summary["node_count"], 5)
        self.assertEqual(summary["edge_count"], 4)
        self.assertIn("entity_types", summary)
        self.assertIn("relationship_types", summary)
        self.assertIn("central_entities", summary)
        self.assertGreater(len(summary["central_entities"]), 0)
        self.assertEqual(summary["sections"], 2)
        self.assertEqual(summary["subsections"], 4) # 2 in section 1, 2 in section 2


    # Create a simplified test that doesn't depend on mocking the import
    def test_find_communities_louvain_success(self):
        # Create a test connection between the components to make sure they're in the same community
        # First, make sure we have isolated components for testing
        # Add an edge between ai and feedback (normally not connected)
        self.engine.graph.add_edge("ai", "feedback", label="test_edge", id=str(uuid.uuid4()))
        
        # Call the method (which will use the fallback connected components)
        communities = self.engine.find_communities()
        
        # Check that we have at least one community containing our nodes
        found_community = False
        for community_id, nodes in communities.items():
            if "feedback" in nodes and "ai" in nodes:
                found_community = True
                # All nodes should be in this community
                self.assertEqual(set(nodes), {'feedback', 'control_theory', 'robotics', 'homeostasis', 'ai'})
                break
                
        self.assertTrue(found_community, "Failed to find a community containing both feedback and ai")
        
        # Clean up the test edge
        self.engine.graph.remove_edge("ai", "feedback")

    # CORRECTED: Use the correct patch and raise ImportError for fallback testing
    @patch('app.models.query_engine.community_louvain', create=True)
    def test_find_communities_fallback(self, mock_community_module): # Renamed mock for clarity
        # Simulate ImportError when the community_louvain module is imported
        mock_community_module.__bool__.return_value = False
        mock_community_module.best_partition.side_effect = ImportError("No module named community_louvain")

        # Example: Add an isolated node to test component separation
        self.engine.graph.add_node("isolated_node")

        communities = self.engine.find_communities()

        # Should fall back to connected components
        self.assertGreaterEqual(len(communities), 1) # At least 1 component
        found_main_component = False
        found_isolated_component = False
        expected_main_component = {'feedback', 'control_theory', 'homeostasis', 'robotics', 'ai'}
        for comp_id, nodes in communities.items():
            nodeset = set(nodes)
            if "feedback" in nodeset: # Check if it's the main component
                self.assertEqual(nodeset, expected_main_component)
                found_main_component = True
            if "isolated_node" in nodeset and len(nodeset) == 1:
                found_isolated_component = True

        self.assertTrue(found_main_component)
        if "isolated_node" in self.engine.graph:
            self.assertTrue(found_isolated_component)
            self.engine.graph.remove_node("isolated_node") # Clean up


    # --- Structured Ontology Tests ---
    def test_get_subsection_content_success(self):
        content = self.engine.get_subsection_content(1, "Feedback Loops")
        self.assertIsInstance(content, list)
        self.assertEqual(len(content), 3)
        self.assertIn("Homeostasis", content)

        # Test case-insensitivity
        content_case = self.engine.get_subsection_content(1, "feedback loops")
        self.assertEqual(content, content_case)

    def test_get_subsection_content_not_found(self):
        content = self.engine.get_subsection_content(1, "NonExistent")
        self.assertEqual(content, [])
        content = self.engine.get_subsection_content(99, "Feedback Loops")
        self.assertEqual(content, [])

    def test_find_section_by_topic(self):
        # Topic in section title
        results = self.engine.find_section_by_topic("Principles")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["section_num"], "1")
        self.assertTrue(results[0]["title_match"])

        # Topic in subsection name
        results = self.engine.find_section_by_topic("Robotics")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["section_num"], "2")
        self.assertFalse(results[0]["title_match"])
        self.assertGreater(len(results[0]["subsection_matches"]), 0)
        self.assertEqual(results[0]["subsection_matches"][0]["type"], "subsection_title")
        self.assertEqual(results[0]["subsection_matches"][0]["name"], "Robotics")


        # Topic in subsection item (case-insensitive)
        results = self.engine.find_section_by_topic("pid controllers")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["section_num"], "1")
        self.assertFalse(results[0]["title_match"])
        self.assertGreater(len(results[0]["subsection_matches"]), 0)
        match = results[0]["subsection_matches"][0]
        self.assertEqual(match["type"], "item")
        self.assertEqual(match["name"], "Control Theory")
        self.assertEqual(match["item"], "PID Controllers")

        # Topic not found
        results = self.engine.find_section_by_topic("Quantum")
        self.assertEqual(len(results), 0)

    # --- CRUD Entity Tests ---
    def test_create_entity_success(self):
        initial_nodes = self.engine.graph.number_of_nodes()
        entity_data = {
            "label": "New Concept",
            "type": "concept",
            "description": "A fresh idea.",
            "attributes": {"importance": 5}
        }
        created = self.engine.create_entity(entity_data)

        self.assertEqual(self.engine.graph.number_of_nodes(), initial_nodes + 1)
        self.assertIn("id", created)
        new_id = created["id"]
        self.assertTrue(self.engine.graph.has_node(new_id))
        node_attrs = self.engine.graph.nodes[new_id]
        self.assertEqual(node_attrs["label"], "New Concept")
        self.assertEqual(node_attrs["type"], "concept")
        self.assertEqual(node_attrs["description"], "A fresh idea.")
        self.assertEqual(node_attrs["importance"], 5)
        self.assertIn("created_at", node_attrs)
        # Check ID generation from label
        self.assertEqual(new_id, "new_concept") # Simple case

    def test_create_entity_with_id(self):
         entity_data = { "id": "custom_id", "label": "Custom", "type": "test"}
         created = self.engine.create_entity(entity_data)
         self.assertEqual(created["id"], "custom_id")
         self.assertTrue(self.engine.graph.has_node("custom_id"))

    def test_create_entity_duplicate_id_fails(self):
        with self.assertRaises(ValueError) as cm:
            self.engine.create_entity({"id": "feedback", "label": "Duplicate"})
        self.assertIn("already exists", str(cm.exception))

    def test_create_entity_duplicate_label_generates_unique_id(self):
         created1 = self.engine.create_entity({"label": "Duplicate Label", "type": "test"})
         created2 = self.engine.create_entity({"label": "Duplicate Label", "type": "test"})
         self.assertEqual(created1["id"], "duplicate_label")
         self.assertNotEqual(created1["id"], created2["id"])
         self.assertTrue(created2["id"].startswith("duplicate_label_")) # Check for suffix
         self.assertTrue(self.engine.graph.has_node(created1["id"]))
         self.assertTrue(self.engine.graph.has_node(created2["id"]))


    def test_update_entity_success(self):
        update_data = {
            "label": "Updated Feedback",
            "description": "An updated description.",
            "attributes": {"new_attr": "value", "importance": 10} # Add new, update existing
        }
        updated = self.engine.update_entity("feedback", update_data)

        self.assertIsNotNone(updated)
        self.assertEqual(updated["id"], "feedback")
        node_attrs = self.engine.graph.nodes["feedback"]
        self.assertEqual(node_attrs["label"], "Updated Feedback")
        self.assertEqual(node_attrs["description"], "An updated description.")
        self.assertEqual(node_attrs["new_attr"], "value") # Check added attribute
        self.assertEqual(node_attrs.get("importance"), 10) # Check updated custom attribute (if it existed)
        self.assertIn("updated_at", node_attrs)
        self.assertNotEqual(node_attrs.get("created_at"), node_attrs.get("updated_at"))

    def test_update_entity_not_found(self):
        updated = self.engine.update_entity("nonexistent", {"label": "Wont Work"})
        self.assertIsNone(updated)

    def test_delete_entity_success_no_relations(self):
         # Add node with no relations to delete
        self.engine.create_entity({"id": "to_delete", "label": "Delete Me"})
        initial_nodes = self.engine.graph.number_of_nodes()
        result = self.engine.delete_entity("to_delete")

        self.assertTrue(result["success"])
        self.assertFalse(self.engine.graph.has_node("to_delete"))
        self.assertEqual(self.engine.graph.number_of_nodes(), initial_nodes - 1)

    def test_delete_entity_fail_has_relations_no_cascade(self):
         initial_nodes = self.engine.graph.number_of_nodes()
         initial_edges = self.engine.graph.number_of_edges()
         result = self.engine.delete_entity("feedback") # Has outgoing edges

         self.assertFalse(result["success"])
         self.assertIn("message", result)
         self.assertIn("cascade=true", result["message"])
         self.assertTrue(self.engine.graph.has_node("feedback")) # Should still exist
         self.assertEqual(self.engine.graph.number_of_nodes(), initial_nodes)
         self.assertEqual(self.engine.graph.number_of_edges(), initial_edges)


    def test_delete_entity_success_cascade(self):
         initial_nodes = self.engine.graph.number_of_nodes()
         initial_edges = self.engine.graph.number_of_edges() # feedback has 2 outgoing
         result = self.engine.delete_entity("feedback", cascade=True)

         self.assertTrue(result["success"])
         self.assertEqual(result["relationships_removed"], 2)
         self.assertFalse(self.engine.graph.has_node("feedback"))
         self.assertEqual(self.engine.graph.number_of_nodes(), initial_nodes - 1)
         self.assertEqual(self.engine.graph.number_of_edges(), initial_edges - 2) # Edges should be gone
         # Check one of the target nodes still exists
         self.assertTrue(self.engine.graph.has_node("control_theory"))


    def test_delete_entity_not_found(self):
        result = self.engine.delete_entity("nonexistent")
        self.assertFalse(result["success"])
        self.assertTrue(result["not_found"])

    # --- CRUD Relationship Tests ---
    def test_create_relationship_success(self):
        initial_edges = self.engine.graph.number_of_edges()
        rel_data = {
            "source_id": "homeostasis",
            "target_id": "robotics",
            "relationship_type": "influences",
            "attributes": {"strength": 0.8}
        }
        created = self.engine.create_relationship(rel_data)

        self.assertEqual(self.engine.graph.number_of_edges(), initial_edges + 1)
        self.assertTrue(self.engine.graph.has_edge("homeostasis", "robotics"))
        edge_data = self.engine.graph.get_edge_data("homeostasis", "robotics")
        self.assertEqual(edge_data["label"], "influences")
        self.assertEqual(edge_data["strength"], 0.8)
        self.assertIn("id", edge_data)
        self.assertIn("created_at", edge_data)

        # Check response format
        self.assertEqual(created["source_id"], "homeostasis")
        self.assertEqual(created["target_id"], "robotics")
        self.assertEqual(created["relationship_type"], "influences")
        self.assertEqual(created["attributes"]["strength"], 0.8)
        self.assertIn("id", created)

    def test_create_relationship_node_not_found(self):
        with self.assertRaisesRegex(ValueError, "Source entity .* not found"):
            self.engine.create_relationship({"source_id": "xxx", "target_id": "feedback", "relationship_type": "test"})
        with self.assertRaisesRegex(ValueError, "Target entity .* not found"):
            self.engine.create_relationship({"source_id": "feedback", "target_id": "yyy", "relationship_type": "test"})

    def test_create_relationship_duplicate_fails(self):
        # First edge exists in setup: feedback -> control_theory (is_central_to)
        with self.assertRaisesRegex(ValueError, "Relationship of type 'is_central_to' already exists"):
             self.engine.create_relationship({
                 "source_id": "feedback",
                 "target_id": "control_theory",
                 "relationship_type": "is_central_to" # Same type
             })
        # Should allow different type between same nodes
        try:
            self.engine.create_relationship({
                "source_id": "feedback",
                "target_id": "control_theory",
                "relationship_type": "another_link" # Different type
            })
            self.assertTrue(self.engine.graph.has_edge("feedback", "control_theory"))
             # Need MultiDiGraph to truly test multiple edges, but logic prevents same type
        except ValueError:
             self.fail("Should allow different relationship types between same nodes")


    def test_get_relationship_success(self):
        # Find an existing edge's ID from the sample data edges
        edge_to_find = None
        for u, v, data in self.engine.graph.edges(data=True):
            if u == 'feedback' and v == 'control_theory':
                edge_to_find = data
                break
        self.assertIsNotNone(edge_to_find, "Setup error: Cannot find sample edge")
        edge_id = edge_to_find['id']

        retrieved = self.engine.get_relationship(edge_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["id"], edge_id)
        self.assertEqual(retrieved["source_id"], "feedback")
        self.assertEqual(retrieved["target_id"], "control_theory")
        self.assertEqual(retrieved["relationship_type"], "is_central_to")
        self.assertEqual(retrieved["source_label"], "Feedback")
        self.assertEqual(retrieved["target_label"], "Control Theory")
        self.assertIn("created_at", retrieved)

    def test_get_relationship_not_found(self):
        retrieved = self.engine.get_relationship(str(uuid.uuid4())) # Random UUID
        self.assertIsNone(retrieved)

    def test_update_relationship_success(self):
        # Find an existing edge's ID
        edge_data = next(iter(self.engine.graph.edges(data=True))) # Get first edge
        source, target, data = edge_data
        edge_id = data['id']

        update_data = {
            "relationship_type": "updated_rel",
            "attributes": {"weight": 100, "notes": "test"}
        }
        updated = self.engine.update_relationship(edge_id, update_data)

        self.assertIsNotNone(updated)
        self.assertEqual(updated["id"], edge_id)
        self.assertEqual(updated["relationship_type"], "updated_rel")
        self.assertEqual(updated["attributes"]["weight"], 100)
        self.assertEqual(updated["attributes"]["notes"], "test")
        self.assertIn("updated_at", updated)

        # Verify in graph
        new_edge_data = self.engine.graph.get_edge_data(source, target)
        self.assertEqual(new_edge_data["label"], "updated_rel")
        self.assertEqual(new_edge_data["weight"], 100)
        self.assertIn("updated_at", new_edge_data)

    def test_update_relationship_not_found(self):
        updated = self.engine.update_relationship(str(uuid.uuid4()), {"relationship_type": "x"})
        self.assertIsNone(updated)

    def test_delete_relationship_success(self):
        # Find an existing edge's ID
        edge_data = next(iter(self.engine.graph.edges(data=True))) # Get first edge
        source, target, data = edge_data
        edge_id = data['id']
        initial_edges = self.engine.graph.number_of_edges()

        deleted = self.engine.delete_relationship(edge_id)

        self.assertTrue(deleted)
        self.assertFalse(self.engine.graph.has_edge(source, target))
        self.assertEqual(self.engine.graph.number_of_edges(), initial_edges - 1)

    def test_delete_relationship_not_found(self):
        deleted = self.engine.delete_relationship(str(uuid.uuid4()))
        self.assertFalse(deleted)

    # --- Listing Tests ---
    def test_list_entities_basic(self):
        result = self.engine.list_entities()
        self.assertEqual(len(result["entities"]), 5) # All entities
        self.assertEqual(result["total"], 5)
        self.assertIn("id", result["entities"][0])
        self.assertIn("label", result["entities"][0])
        self.assertIn("type", result["entities"][0])

    def test_list_entities_filter_type(self):
        result = self.engine.list_entities(entity_type="concept")
        self.assertEqual(len(result["entities"]), 2) # feedback, homeostasis
        self.assertEqual(result["total"], 2)
        self.assertTrue(all(e["type"] == "concept" for e in result["entities"]))

    def test_list_entities_filter_query(self):
        result = self.engine.list_entities(query="control") # Matches label and desc?
        # Expected: control_theory (label)
        self.assertEqual(len(result["entities"]), 1)
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["entities"][0]["id"], "control_theory")

        result_desc = self.engine.list_entities(query="stability") # Matches homeostasis description
        self.assertEqual(len(result_desc["entities"]), 1)
        self.assertEqual(result_desc["total"], 1)
        self.assertEqual(result_desc["entities"][0]["id"], "homeostasis")

    def test_list_entities_pagination(self):
        result = self.engine.list_entities(limit=2, offset=1, sort='label', order='asc') # Sort to ensure consistency
        self.assertEqual(len(result["entities"]), 2)
        self.assertEqual(result["total"], 5)
        # Assuming alphabetical: AI, Control Theory, Feedback, Homeostasis, Robotics
        # Offset 1, Limit 2 -> Control Theory, Feedback
        self.assertEqual(result["entities"][0]["id"], "control_theory")
        self.assertEqual(result["entities"][1]["id"], "feedback")

    def test_list_entities_sorting(self):
        # Sort by label descending
        result = self.engine.list_entities(sort='label', order='desc', limit=1)
        self.assertEqual(result["entities"][0]["id"], "robotics")

        # Sort by created_at ascending (oldest first)
        result = self.engine.list_entities(sort='created_at', order='asc', limit=1)
        self.assertEqual(result["entities"][0]["id"], "ai") # Oldest

    def test_list_relationships_basic(self):
        result = self.engine.list_relationships()
        self.assertEqual(len(result["relationships"]), 4) # All relationships
        self.assertEqual(result["total"], 4)
        self.assertIn("id", result["relationships"][0])
        self.assertIn("source_id", result["relationships"][0])
        self.assertIn("target_id", result["relationships"][0])
        self.assertIn("relationship_type", result["relationships"][0])

    def test_list_relationships_filter_source(self):
        result = self.engine.list_relationships(source_id="feedback")
        self.assertEqual(len(result["relationships"]), 2) # -> control_theory, -> homeostasis
        self.assertEqual(result["total"], 2)
        self.assertTrue(all(r["source_id"] == "feedback" for r in result["relationships"]))

    def test_list_relationships_filter_target(self):
        result = self.engine.list_relationships(target_id="robotics")
        self.assertEqual(len(result["relationships"]), 2) # control_theory ->, ai ->
        self.assertEqual(result["total"], 2)
        self.assertTrue(all(r["target_id"] == "robotics" for r in result["relationships"]))

    def test_list_relationships_filter_entity_id(self):
         # Should match if entity is source OR target
         result = self.engine.list_relationships(entity_id="control_theory")
         # Edges: feedback -> control_theory, control_theory -> robotics
         self.assertEqual(len(result["relationships"]), 2)
         self.assertEqual(result["total"], 2)
         ids_involved = {r["source_id"] for r in result["relationships"]} | {r["target_id"] for r in result["relationships"]}
         self.assertIn("control_theory", ids_involved)


    def test_list_relationships_filter_type(self):
        result = self.engine.list_relationships(relationship_type="applied_in")
        self.assertEqual(len(result["relationships"]), 1)
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["relationships"][0]["relationship_type"], "applied_in")
        self.assertEqual(result["relationships"][0]["source_id"], "control_theory")

    def test_list_relationships_pagination_and_sorting(self):
        # Sort by type ascending, get page 2
        result = self.engine.list_relationships(limit=2, offset=2, sort='relationship_type', order='asc')
        self.assertEqual(len(result["relationships"]), 2)
        self.assertEqual(result["total"], 4)
        # Assuming alphabetical type order: applied_in, enables, is_central_to, related_to
        # Offset 2, Limit 2 -> is_central_to, related_to
        self.assertEqual(result["relationships"][0]["relationship_type"], "is_central_to")
        self.assertEqual(result["relationships"][1]["relationship_type"], "related_to")


    # --- Persistence Test ---
    @patch("builtins.open", new_callable=mock_open) # Mock open for writing
    @patch("json.dump") # Mock json.dump to avoid actual serialization
    def test_save_changes(self, mock_json_dump, mock_file_open):
        # Modify the graph slightly
        self.engine.create_entity({"id": "save_test", "label": "Save Test"})
        self.assertTrue(self.engine.graph.has_node("save_test"))

        # Call save_changes
        success = self.engine.save_changes()
        self.assertTrue(success)

        # Assert 'open' was called correctly for writing
        mock_file_open.assert_called_once_with("fake_path.json", 'w', encoding='utf-8')

        # Get the handle that 'open' returned
        mock_file_handle = mock_file_open()

        # Check json.dump was called with self.data as first arg and file handle as second arg
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        data_arg, file_arg = args
        
        # Check data_arg has the right structure
        self.assertIn("structured_ontology", data_arg)
        self.assertIn("knowledge_graph", data_arg)

        # Check knowledge_graph structure (node-link format)
        kg_data = data_arg["knowledge_graph"]
        self.assertTrue(kg_data.get("directed"))
        self.assertFalse(kg_data.get("multigraph"))
        self.assertIn("nodes", kg_data)
        self.assertIn("edges", kg_data) 
        self.assertGreater(len(kg_data["nodes"]), 5) # Should include the new node

        # Verify the saved node exists
        saved_node_ids = {n.get('id') for n in kg_data["nodes"]}
        self.assertIn("save_test", saved_node_ids)


if __name__ == "__main__":
    unittest.main()