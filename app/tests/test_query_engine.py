import unittest
import pytest
import networkx as nx
import json
from unittest.mock import patch, mock_open
from app.models.query_engine import CyberneticsQueryEngine 

SAMPLE_DATA = {
    "structured_ontology": {
        "1": {
            "title": "Test Section",
            "subsections": {
                "Test Subsection": ["Item 1", "Item 2"] # Assuming items were simple strings before
                # If items were complex dicts, adjust structured_ontology as needed
            }
        }
    },
    "knowledge_graph": {
        # --- Node-Link Format Specific Keys ---
        "directed": True,      # <--- Crucial: Ensures DiGraph is created
        "multigraph": False,   # <--- Crucial: Ensures DiGraph (not MultiDiGraph)
        "graph": {},           # Standard part of the format (can hold graph attributes)
        # --- Nodes ---
        "nodes": [
            {"id": "node1", "label": "First Node", "type": "concept"},
            {"id": "node2", "label": "Second Node", "type": "theory"},
            {"id": "node3", "label": "Third Node", "type": "application"},
            {"id": "node4", "label": "Fourth Node", "type": "concept"}
        ],
        # --- Edges  ---
        "edges": [ 
            # Note: Edge attributes like 'label' are properties of the edge object
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
        # Mock the file open to return our UPDATED sample data
        # The engine's load_data should now use nx.node_link_graph
        # which correctly interprets the "directed" and "multigraph" flags.
        m = mock_open(read_data=json.dumps(SAMPLE_DATA))
        with patch("builtins.open", m):
            # Assume CyberneticsQueryEngine.__init__ calls load_data which now
            # uses nx.node_link_graph(data['knowledge_graph'])
            self.engine = CyberneticsQueryEngine("fake_path.json") 
        
        # --- Verification after load ---
        # Check graph type explicitly
        self.assertIsInstance(self.engine.graph, nx.DiGraph, "Graph should be loaded as DiGraph")
        self.assertTrue(self.engine.graph.is_directed(), "Graph should be directed")
        self.assertFalse(self.engine.graph.is_multigraph(), "Graph should not be a multigraph")

        # Verify the graph was built correctly (counts should remain the same)
        self.assertEqual(len(self.engine.graph.nodes), 4)
        self.assertEqual(len(self.engine.graph.edges), 4)
    
    def test_query_entity_success(self):
        """Test successfully querying a single entity"""
        result = self.engine.query_entity("node1")
        
        # Verify the result structure (No change needed here)
        self.assertEqual(result["id"], "node1")
        self.assertEqual(result["attributes"]["label"], "First Node")
        self.assertEqual(result["attributes"]["type"], "concept")
        
        # Verify connections (Should work correctly now)
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
        
        # Should find at least one path (No change needed here)
        self.assertGreater(len(paths), 0)
        
        # Verify the first path
        first_path = paths[0]
        self.assertEqual(first_path[0]["id"], "node1")
        self.assertEqual(first_path[-1]["id"], "node3")
        
        # Verify relationship information
        self.assertIn("relationship_to_next", first_path[0])
        self.assertIn("relationship_to_next", first_path[1]) # Check intermediate node too

        # Check specific paths (optional, but good)
        path_strings = ["->".join([n['id'] for n in p]) for p in paths]
        self.assertIn("node1->node2->node3", path_strings)
        self.assertIn("node1->node4->node3", path_strings)

    
    def test_find_paths_no_path(self):
        """Test finding paths when no path exists"""
        # Create a disconnected node (No change needed here)
        self.engine.graph.add_node("isolated", label="Isolated Node", type="concept")
        
        paths = self.engine.find_paths("node1", "isolated", max_length=3)
        self.assertEqual(len(paths), 0)
        
        # Clean up added node
        self.engine.graph.remove_node("isolated")

    def test_find_connections(self):
        """Test finding connections within a distance"""
        connections = self.engine.find_connections("node1", max_distance=2)
        
        # Should find connections at distance 1 (No change needed here)
        self.assertIn(1, connections)
        self.assertEqual(len(connections[1]), 2)  # node2 and node4
        
        # Should find connections at distance 2
        self.assertIn(2, connections)
        self.assertEqual(len(connections[2]), 1)  # node3 (via node2 or node4)
        self.assertEqual(connections[2][0]['id'], 'node3')
        
        # Check for specific nodes
        distance_1_ids = [node["id"] for node in connections[1]]
        self.assertIn("node2", distance_1_ids)
        self.assertIn("node4", distance_1_ids)
    
    def test_search_entities(self):
        """Test searching for entities by name"""
        results = self.engine.search_entities("node")
        
        # Should find all nodes (No change needed here)
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
        
        # Should return 2 entities (No change needed here)
        self.assertEqual(len(central), 2)
        
        # Each entity should have centrality score and connections count
        for entity in central:
            self.assertIn("centrality", entity)
            self.assertIn("connections", entity)

        # Optionally check which nodes are most central (node1/node3 likely)
        central_ids = {e['id'] for e in central}
        # Based on DiGraph: node1 (out=2), node2 (in=1,out=1), node3(in=2), node4(in=1,out=1)
        # Degree Centrality (normalized by N-1=3): node1=2/3, node2=2/3, node3=2/3, node4=2/3
        # Okay, degree centrality might be equal for all in this small graph. Let's check connections.
        self.assertTrue(all(e['connections'] == 2 for e in central)) # Check if top 2 have degree 2

    
    def test_get_related_concepts(self):
        """Test getting related concepts"""
        # THIS TEST SHOULD NOW PASS
        related = self.engine.get_related_concepts("node1") 
        
        # Should have outgoing relationships
        self.assertIn("related_to", related)
        self.assertIn("evolved_into", related)
        
        # Check a specific relationship
        self.assertEqual(len(related["evolved_into"]), 1)
        self.assertEqual(related["evolved_into"][0]["id"], "node4")
        self.assertEqual(related["evolved_into"][0]["direction"], "outgoing")

        # Check incoming relationships for node 3
        related_node3 = self.engine.get_related_concepts("node3")
        self.assertIn("inverse_implements", related_node3) # From node2
        self.assertIn("inverse_is_used_by", related_node3) # From node4
        self.assertEqual(len(related_node3["inverse_implements"]), 1)
        self.assertEqual(related_node3["inverse_implements"][0]["id"], "node2")
        self.assertEqual(related_node3["inverse_implements"][0]["direction"], "incoming")

        # Test with relationship type filter
        related = self.engine.get_related_concepts("node1", relationship_types=["evolved_into"])
        self.assertIn("evolved_into", related)
        self.assertNotIn("related_to", related) # Should not include other types
        self.assertEqual(len(related), 1) # Only one key should be present
    
    def test_trace_evolution_chain(self):
        """Test tracing an evolution chain"""
        # This test uses the private method _trace_evolution_chain
        # It relies on out_edges, so should work now.
        chain = self.engine._trace_evolution_chain("node1") 
        
        # Chain should start with node1
        self.assertEqual(chain[0]["id"], "node1")
        
        # Chain should include node4 (evolved_into)
        self.assertEqual(chain[1]["id"], "node4")
        
        # Length should be 2 (node4 does not evolve further in sample)
        self.assertEqual(len(chain), 2)

    # Consider adding tests for CRUD operations if not already done elsewhere

if __name__ == "__main__":
    unittest.main()