import unittest
import pytest
import networkx as nx
import json
from unittest.mock import patch, mock_open
from app.models.query_engine import CyberneticsQueryEngine

# Sample data for tests
SAMPLE_DATA = {
    "structured_ontology": {
        "1": {
            "title": "Test Section",
            "subsections": {
                "Test Subsection": ["Item 1", "Item 2"]
            }
        }
    },
    "knowledge_graph": {
        "nodes": [
            {"id": "node1", "label": "First Node", "type": "concept"},
            {"id": "node2", "label": "Second Node", "type": "theory"},
            {"id": "node3", "label": "Third Node", "type": "application"},
            {"id": "node4", "label": "Fourth Node", "type": "concept"}
        ],
        "edges": [
            {"source": "node1", "target": "node2", "label": "related_to"},
            {"source": "node2", "target": "node3", "label": "implements"},
            {"source": "node1", "target": "node4", "label": "evolved_into"},
            {"source": "node4", "target": "node3", "label": "is_used_by"}
        ]
    }
}

class TestCyberneticsQueryEngine(unittest.TestCase):
    """Tests for the CyberneticsQueryEngine class"""

    def setUp(self):
        """Set up test environment"""
        # Mock the file open to return our sample data
        with patch("builtins.open", mock_open(read_data=json.dumps(SAMPLE_DATA))):
            self.engine = CyberneticsQueryEngine("fake_path.json")
        
        # Verify the graph was built correctly
        self.assertEqual(len(self.engine.graph.nodes), 4)
        self.assertEqual(len(self.engine.graph.edges), 4)
    
    def test_query_entity_success(self):
        """Test successfully querying a single entity"""
        result = self.engine.query_entity("node1")
        
        # Verify the result structure
        self.assertEqual(result["id"], "node1")
        self.assertEqual(result["attributes"]["label"], "First Node")
        self.assertEqual(result["attributes"]["type"], "concept")
        
        # Verify connections
        self.assertEqual(len(result["incoming"]), 0)
        self.assertEqual(len(result["outgoing"]), 2)
        
        # Check outgoing connections
        outgoing_ids = [conn["id"] for conn in result["outgoing"]]
        self.assertIn("node2", outgoing_ids)
        self.assertIn("node4", outgoing_ids)
    
    def test_query_entity_not_found(self):
        """Test querying a non-existent entity"""
        result = self.engine.query_entity("nonexistent")
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Entity 'nonexistent' not found")
    
    def test_find_paths_success(self):
        """Test finding paths between entities"""
        paths = self.engine.find_paths("node1", "node3", max_length=3)
        
        # Should find at least one path
        self.assertGreater(len(paths), 0)
        
        # Verify the first path
        first_path = paths[0]
        self.assertEqual(first_path[0]["id"], "node1")
        self.assertEqual(first_path[-1]["id"], "node3")
        
        # Verify relationship information
        self.assertIn("relationship_to_next", first_path[0])
    
    def test_find_paths_no_path(self):
        """Test finding paths when no path exists"""
        # Create a disconnected node
        self.engine.graph.add_node("isolated", label="Isolated Node", type="concept")
        
        paths = self.engine.find_paths("node1", "isolated", max_length=3)
        self.assertEqual(len(paths), 0)
    
    def test_find_connections(self):
        """Test finding connections within a distance"""
        connections = self.engine.find_connections("node1", max_distance=2)
        
        # Should find connections at distance 1
        self.assertIn(1, connections)
        self.assertEqual(len(connections[1]), 2)  # node2 and node4
        
        # Should find connections at distance 2
        self.assertIn(2, connections)
        self.assertEqual(len(connections[2]), 1)  # node3
        
        # Check for specific nodes
        distance_1_ids = [node["id"] for node in connections[1]]
        self.assertIn("node2", distance_1_ids)
        self.assertIn("node4", distance_1_ids)
    
    def test_search_entities(self):
        """Test searching for entities by name"""
        results = self.engine.search_entities("node")
        
        # Should find all nodes
        self.assertEqual(len(results), 4)
        
        # Test with specific term
        results = self.engine.search_entities("first")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "node1")
        
        # Test with entity type filter
        results = self.engine.search_entities("node", entity_types=["concept"])
        self.assertEqual(len(results), 2)  # node1 and node4
        result_ids = [r["id"] for r in results]
        self.assertIn("node1", result_ids)
        self.assertIn("node4", result_ids)
    
    def test_get_central_entities(self):
        """Test getting central entities"""
        central = self.engine.get_central_entities(top_n=2)
        
        # Should return 2 entities
        self.assertEqual(len(central), 2)
        
        # Each entity should have centrality score and connections count
        for entity in central:
            self.assertIn("centrality", entity)
            self.assertIn("connections", entity)
    
    def test_get_related_concepts(self):
        """Test getting related concepts"""
        related = self.engine.get_related_concepts("node1")
        
        # Should have outgoing relationships
        self.assertIn("related_to", related)
        self.assertIn("evolved_into", related)
        
        # Check a specific relationship
        self.assertEqual(len(related["evolved_into"]), 1)
        self.assertEqual(related["evolved_into"][0]["id"], "node4")
        self.assertEqual(related["evolved_into"][0]["direction"], "outgoing")
        
        # Test with relationship type filter
        related = self.engine.get_related_concepts("node1", relationship_types=["evolved_into"])
        self.assertIn("evolved_into", related)
        self.assertNotIn("related_to", related)
    
    def test_trace_evolution_chain(self):
        """Test tracing an evolution chain"""
        chain = self.engine._trace_evolution_chain("node1")
        
        # Chain should start with node1
        self.assertEqual(chain[0]["id"], "node1")
        
        # Chain should include node4 (evolved_into)
        self.assertEqual(chain[1]["id"], "node4")
        
        # Length should be 2 (no further evolution)
        self.assertEqual(len(chain), 2)

if __name__ == "__main__":
    unittest.main()