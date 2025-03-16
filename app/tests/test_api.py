import json
import unittest
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask

from app import create_app
from app.routes.api import bp as api_bp
from app.models.query_engine import CyberneticsQueryEngine

# Mark all tests in this module with the 'api' marker
pytestmark = pytest.mark.api


class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        """Set up test client and app context"""
        self.app = create_app(testing=True)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create mock query engine
        self.mock_query_engine = MagicMock(spec=CyberneticsQueryEngine)
        
        # Setup mock graph with sample data
        self.mock_graph = MagicMock()
        self.mock_query_engine.graph = self.mock_graph
        
        # Sample nodes and edges for graph data endpoint
        self.sample_nodes = [
            {"id": "concept1", "label": "First Concept", "type": "concept"}
        ]
        self.sample_edges = [
            {"source": "concept1", "target": "concept2", "label": "related_to"}
        ]
        
        # Configure mock methods to return sample data
        self.mock_graph.nodes.return_value = [{"id": "concept1"}]
        
        # Patch the query_engine in api module
        self.patcher = patch('app.routes.api.query_engine', self.mock_query_engine)
        self.mock_api_query_engine = self.patcher.start()
    
    def tearDown(self):
        """Clean up after tests"""
        self.patcher.stop()
        self.app_context.pop()
    
    def test_get_graph_data(self):
        """Test the /graph-data endpoint"""
        # Setup mock values for graph nodes and edges
        self.mock_graph.nodes.return_value = ["concept1"]
        self.mock_graph.nodes.__getitem__.return_value = {"label": "First Concept", "type": "concept"}
        self.mock_graph.edges.return_value = [("concept1", "concept2", {"label": "related_to"})]
        
        # Make request to endpoint
        response = self.client.get('/api/graph-data')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('nodes', data)
        self.assertIn('links', data)
    
    def test_get_entity(self):
        """Test the /entity/<entity_id> endpoint"""
        # Setup mock query_entity return value
        entity_info = {
            "id": "concept1",
            "attributes": {"label": "First Concept", "type": "concept"},
            "incoming": [],
            "outgoing": []
        }
        self.mock_query_engine.query_entity.return_value = entity_info
        
        # Make request to endpoint
        response = self.client.get('/api/entity/concept1')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, entity_info)
        self.mock_query_engine.query_entity.assert_called_once_with("concept1")
    
    def test_search(self):
        """Test the /search endpoint"""
        # Setup mock search_entities return value
        search_results = [
            {"id": "concept1", "label": "First Concept", "type": "concept", "match_score": 1.0}
        ]
        self.mock_query_engine.search_entities.return_value = search_results
        
        # Make request to endpoint
        response = self.client.get('/api/search?q=concept&types=concept,theory')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('results', data)
        self.assertEqual(data['results'], search_results)
        self.mock_query_engine.search_entities.assert_called_once_with("concept", ["concept", "theory"])
    
    def test_find_paths(self):
        """Test the /paths endpoint"""
        # Setup mock find_paths return value
        paths = [
            [
                {"id": "concept1", "label": "First Concept", "type": "concept", "relationship_to_next": "related_to"},
                {"id": "concept2", "label": "Second Concept", "type": "concept"}
            ]
        ]
        self.mock_query_engine.find_paths.return_value = paths
        
        # Make request to endpoint
        response = self.client.get('/api/paths?source=concept1&target=concept2&max_length=2')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('paths', data)
        self.assertEqual(data['paths'], paths)
        self.mock_query_engine.find_paths.assert_called_once_with("concept1", "concept2", 2)
    
    def test_find_sections(self):
        """Test the /sections/topic/<topic> endpoint"""
        # Setup mock find_section_by_topic return value
        sections = [
            {
                "section_num": "1",
                "title": "Introduction to Cybernetics",
                "title_match": True,
                "subsection_matches": []
            }
        ]
        self.mock_query_engine.find_section_by_topic.return_value = sections
        
        # Make request to endpoint
        response = self.client.get('/api/sections/topic/cybernetics')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('sections', data)
        self.assertEqual(data['sections'], sections)
        self.mock_query_engine.find_section_by_topic.assert_called_once_with("cybernetics")
    
    def test_get_concept_evolution(self):
        """Test the /concepts/evolution endpoint"""
        # Setup mock get_concept_evolution return value
        evolution_chains = [
            [
                {"id": "concept1", "label": "First Generation", "type": "concept"},
                {"id": "concept2", "label": "Second Generation", "type": "concept"}
            ]
        ]
        self.mock_query_engine.get_concept_evolution.return_value = evolution_chains
        
        # Make request to endpoint
        response = self.client.get('/api/concepts/evolution')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('evolution_chains', data)
        self.assertEqual(data['evolution_chains'], evolution_chains)
        self.mock_query_engine.get_concept_evolution.assert_called_once()
    
    def test_get_central_concepts(self):
        """Test the /concepts/central endpoint"""
        # Setup mock get_central_entities return value
        central_entities = [
            {"id": "concept1", "label": "Central Concept", "type": "concept", "centrality": 0.8, "connections": 15}
        ]
        self.mock_query_engine.get_central_entities.return_value = central_entities
        
        # Make request to endpoint
        response = self.client.get('/api/concepts/central?count=5')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('central_entities', data)
        self.assertEqual(data['central_entities'], central_entities)
        self.mock_query_engine.get_central_entities.assert_called_once_with(5)
    
    def test_get_related_concepts(self):
        """Test the /concepts/related/<concept_id> endpoint"""
        # Setup mock get_related_concepts return value
        related_concepts = {
            "is_part_of": [
                {"id": "concept2", "label": "Parent Concept", "type": "concept", "direction": "outgoing"}
            ],
            "has_part": [
                {"id": "concept3", "label": "Child Concept", "type": "concept", "direction": "outgoing"}
            ]
        }
        self.mock_query_engine.get_related_concepts.return_value = related_concepts
        
        # Make request to endpoint
        response = self.client.get('/api/concepts/related/concept1?types=is_part_of,has_part')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, related_concepts)
        self.mock_query_engine.get_related_concepts.assert_called_once_with("concept1", ["is_part_of", "has_part"])
    
    def test_get_hierarchy(self):
        """Test the /hierarchy endpoint"""
        # Setup mock analyze_concept_hierarchy return value
        hierarchy = {
            "root_nodes": [
                {"id": "concept1", "label": "Root Concept", "type": "concept", "max_depth": 3}
            ],
            "hierarchies": {
                "concept1": {
                    "0": [{"id": "concept1", "label": "Root Concept", "type": "concept"}],
                    "1": [{"id": "concept2", "label": "Child Concept", "type": "concept"}]
                }
            }
        }
        self.mock_query_engine.analyze_concept_hierarchy.return_value = hierarchy
        
        # Make request to endpoint
        response = self.client.get('/api/hierarchy')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, hierarchy)
        self.mock_query_engine.analyze_concept_hierarchy.assert_called_once()
    
    def test_no_ontology_data(self):
        """Test endpoints when no ontology data is loaded"""
        # Set query_engine to None to simulate no data loaded
        self.patcher.stop()
        with patch('app.routes.api.query_engine', None):
            # Test one of the endpoints
            response = self.client.get('/api/graph-data')
            
            # Check response
            self.assertEqual(response.status_code, 404)
            data = json.loads(response.data)
            self.assertIn('error', data)
            self.assertEqual(data['error'], "No ontology data loaded")
        
        # Restart the original patcher for other tests
        self.patcher.start()


if __name__ == '__main__':
    unittest.main()