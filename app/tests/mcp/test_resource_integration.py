"""
Tests for MCP resource handlers.

This module contains tests for the MCP resource handlers.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from app.mcp.handlers.resources import (
    list_resources_handler,
    list_resource_templates_handler,
    read_resource_handler,
    resource_subscription_handler,
    resource_unsubscription_handler,
    set_query_engine
)

class MockNode:
    """Mock class for NetworkX nodes."""
    def __init__(self, node_id, attrs):
        self.id = node_id
        self.attrs = attrs
        
    def __getitem__(self, key):
        return self.attrs.get(key)

class MockGraph:
    """Mock graph for testing."""
    def __init__(self):
        self.nodes_data = {
            "node1": {"label": "Entity 1", "type": "concept"},
            "node2": {"label": "Entity 2", "type": "person"},
            "node3": {"label": "Entity 3", "type": "concept"}
        }
        
        self.edges_data = [
            ("node1", "node2", {"id": "edge1", "label": "related_to"}),
            ("node2", "node3", {"id": "edge2", "label": "created_by"}),
            ("node1", "node3", {"id": "edge3", "label": "related_to"})
        ]
    
    def nodes(self, data=False):
        if data:
            return [(node_id, attrs) for node_id, attrs in self.nodes_data.items()]
        return self.nodes_data.keys()
    
    def edges(self, data=False):
        if data:
            return self.edges_data
        return [(src, tgt) for src, tgt, _ in self.edges_data]

class MockQueryEngine:
    """Mock query engine for testing."""
    def __init__(self):
        self.graph = MockGraph()
        self.structured_ontology = {
            1: {
                "title": "Introduction",
                "subsections": {
                    "Overview": ["Item 1", "Item 2"],
                    "History": ["Item 3", "Item 4"]
                }
            },
            2: {
                "title": "Core Concepts",
                "subsections": {
                    "Definitions": ["Item 5", "Item 6"],
                    "Principles": ["Item 7", "Item 8"]
                }
            }
        }
    
    def get_entity_types(self):
        types = {}
        for _, attrs in self.graph.nodes(data=True):
            entity_type = attrs.get("type", "unknown")
            types[entity_type] = types.get(entity_type, 0) + 1
        return types
    
    def get_relationship_types(self):
        types = {}
        for _, _, data in self.graph.edges(data=True):
            rel_type = data.get("label", "unknown")
            types[rel_type] = types.get(rel_type, 0) + 1
        return types
    
    def query_entity(self, entity_id):
        if entity_id not in self.graph.nodes_data:
            return {"error": f"Entity '{entity_id}' not found"}
        
        return {
            "id": entity_id,
            "attributes": self.graph.nodes_data[entity_id],
            "incoming": [],
            "outgoing": []
        }
    
    def search_entities(self, query, entity_types=None):
        results = []
        for node_id, attrs in self.graph.nodes(data=True):
            label = attrs.get("label", "").lower()
            node_type = attrs.get("type", "unknown")
            
            if entity_types and node_type not in entity_types:
                continue
                
            if query.lower() in label:
                results.append({
                    "id": node_id,
                    "label": attrs.get("label", node_id),
                    "type": node_type,
                    "match_score": 1.0 if label == query.lower() else 0.5
                })
        
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results
    
    def get_relationship(self, relationship_id):
        for source, target, data in self.graph.edges(data=True):
            if data.get("id") == relationship_id:
                return {
                    "id": relationship_id,
                    "source": source,
                    "target": target,
                    "relationship_type": data.get("label", "related_to")
                }
        return None
    
    def get_central_entities(self, top_n=5):
        # Mock implementation for testing
        return [
            {"id": "node1", "label": "Entity 1", "type": "concept", "centrality": 0.8, "connections": 2},
            {"id": "node2", "label": "Entity 2", "type": "person", "centrality": 0.5, "connections": 2}
        ]
    
    def get_subsection_content(self, section_num, subsection_name):
        if section_num not in self.structured_ontology:
            return []
            
        section = self.structured_ontology[section_num]
        subsections = section.get("subsections", {})
        
        if subsection_name in subsections:
            return subsections[subsection_name]
        
        return []
    
    def find_paths(self, source_id, target_id, max_length=3):
        # Mock implementation for testing
        return [
            [
                {"id": source_id, "label": self.graph.nodes_data.get(source_id, {}).get("label", source_id)},
                {"id": target_id, "label": self.graph.nodes_data.get(target_id, {}).get("label", target_id)}
            ]
        ]
    
    def find_connections(self, entity_id, max_distance=2):
        # Mock implementation for testing
        return {
            1: [
                {"id": "node2", "label": "Entity 2", "type": "person"}
            ]
        }
    
    def generate_ontology_summary(self):
        # Mock implementation for testing
        return {
            "node_count": len(self.graph.nodes_data),
            "edge_count": len(self.graph.edges_data),
            "entity_types": self.get_entity_types(),
            "relationship_types": self.get_relationship_types()
        }

class TestResourceHandlers(unittest.TestCase):
    """Test MCP resource handlers."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.query_engine = MockQueryEngine()
        set_query_engine(self.query_engine)
        self.transport_id = "test_transport"
    
    def test_list_resources(self):
        """Test the list_resources_handler."""
        result = list_resources_handler({}, self.transport_id)
        
        self.assertIn("resources", result)
        self.assertIsInstance(result["resources"], list)
        self.assertGreater(len(result["resources"]), 0)
        
        # Check that we have a mixture of resource types
        resource_uris = [r["uri"] for r in result["resources"]]
        self.assertTrue(any(uri.startswith("cyberon:///entity_type/") for uri in resource_uris))
        self.assertTrue(any(uri.startswith("cyberon:///relationship_type/") for uri in resource_uris))
        self.assertTrue(any(uri.startswith("cyberon:///section/") for uri in resource_uris))
    
    def test_list_resource_templates(self):
        """Test the list_resource_templates_handler."""
        result = list_resource_templates_handler({}, self.transport_id)
        
        self.assertIn("resourceTemplates", result)
        self.assertIsInstance(result["resourceTemplates"], list)
        self.assertGreater(len(result["resourceTemplates"]), 0)
        
        # Check that we have a mixture of template types
        template_uris = [t["uriTemplate"] for t in result["resourceTemplates"]]
        self.assertTrue(any(uri.startswith("cyberon:///entity/") for uri in template_uris))
        self.assertTrue(any(uri.startswith("cyberon:///relationship/") for uri in template_uris))
        self.assertTrue(any(uri.startswith("cyberon:///section/") for uri in template_uris))
    
    def test_read_entity_resource(self):
        """Test reading an entity resource."""
        params = {"uri": "cyberon:///entity/node1"}
        result = read_resource_handler(params, self.transport_id)
        
        self.assertIn("contents", result)
        self.assertEqual(len(result["contents"]), 1)
        
        content = result["contents"][0]
        self.assertEqual(content["uri"], "cyberon:///entity/node1")
        self.assertEqual(content["mimeType"], "application/json")
        
        # Parse the JSON text
        data = json.loads(content["text"])
        self.assertEqual(data["id"], "node1")
        self.assertEqual(data["attributes"]["label"], "Entity 1")
    
    def test_read_section_resource(self):
        """Test reading a section resource."""
        params = {"uri": "cyberon:///section/1"}
        result = read_resource_handler(params, self.transport_id)
        
        self.assertIn("contents", result)
        self.assertEqual(len(result["contents"]), 1)
        
        content = result["contents"][0]
        self.assertEqual(content["uri"], "cyberon:///section/1")
        self.assertEqual(content["mimeType"], "application/json")
        
        # Parse the JSON text
        data = json.loads(content["text"])
        self.assertEqual(data["title"], "Introduction")
        self.assertIn("subsections", data)
        self.assertIn("Overview", data["subsections"])
    
    def test_read_subsection_resource(self):
        """Test reading a subsection resource."""
        params = {"uri": "cyberon:///section/1/Overview"}
        result = read_resource_handler(params, self.transport_id)
        
        self.assertIn("contents", result)
        self.assertEqual(len(result["contents"]), 1)
        
        content = result["contents"][0]
        self.assertEqual(content["uri"], "cyberon:///section/1/Overview")
        self.assertEqual(content["mimeType"], "application/json")
        
        # Parse the JSON text
        data = json.loads(content["text"])
        self.assertEqual(data["section_num"], 1)
        self.assertEqual(data["section_title"], "Introduction")
        self.assertEqual(data["subsection"], "Overview")
        self.assertEqual(data["content"], ["Item 1", "Item 2"])
    
    def test_read_entity_search_resource(self):
        """Test reading an entity search resource."""
        params = {"uri": "cyberon:///entity/search?query=entity"}
        result = read_resource_handler(params, self.transport_id)
        
        self.assertIn("contents", result)
        self.assertEqual(len(result["contents"]), 1)
        
        content = result["contents"][0]
        self.assertEqual(content["uri"], "cyberon:///entity/search?query=entity")
        self.assertEqual(content["mimeType"], "application/json")
        
        # Parse the JSON text
        data = json.loads(content["text"])
        self.assertEqual(data["query"], "entity")
        self.assertIn("results", data)
        self.assertTrue(len(data["results"]) > 0)
    
    def test_read_graph_summary_resource(self):
        """Test reading a graph summary resource."""
        params = {"uri": "cyberon:///graph/summary"}
        result = read_resource_handler(params, self.transport_id)
        
        self.assertIn("contents", result)
        self.assertEqual(len(result["contents"]), 1)
        
        content = result["contents"][0]
        self.assertEqual(content["uri"], "cyberon:///graph/summary")
        self.assertEqual(content["mimeType"], "application/json")
        
        # Parse the JSON text
        data = json.loads(content["text"])
        self.assertIn("node_count", data)
        self.assertIn("edge_count", data)
        self.assertIn("entity_types", data)
        self.assertIn("relationship_types", data)
    
    def test_resource_subscription(self):
        """Test resource subscription."""
        params = {"uri": "cyberon:///entity/node1"}
        result = resource_subscription_handler(params, self.transport_id)
        
        # For now, just a simple test that it doesn't error
        self.assertEqual(result, {})
    
    def test_resource_unsubscription(self):
        """Test resource unsubscription."""
        params = {"uri": "cyberon:///entity/node1"}
        result = resource_unsubscription_handler(params, self.transport_id)
        
        # For now, just a simple test that it doesn't error
        self.assertEqual(result, {})

if __name__ == "__main__":
    unittest.main()