import json
import unittest
import pytest
from unittest.mock import patch, MagicMock

from app import create_app
from app.models.query_engine import CyberneticsQueryEngine

# Mark all tests in this module with the 'api' marker
pytestmark = pytest.mark.api


class TestGraphAPI(unittest.TestCase):
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
        
        # Patch the query_engine in main module
        self.patcher = patch('app.routes.main.query_engine', self.mock_query_engine)
        self.mock_api_query_engine = self.patcher.start()
        
        # Configure sample entity data
        self.entity1 = {
            "id": "entity1",
            "attributes": {"label": "Entity 1", "type": "concept"},
            "incoming": [],
            "outgoing": []
        }
        
        self.entity2 = {
            "id": "entity2",
            "attributes": {"label": "Entity 2", "type": "concept"},
            "incoming": [],
            "outgoing": []
        }
        
        # Configure mock query_entity to return sample entities
        self.mock_query_engine.query_entity.side_effect = lambda id: (
            self.entity1 if id == "entity1" else 
            (self.entity2 if id == "entity2" else {"error": f"Entity '{id}' not found"})
        )
    
    def tearDown(self):
        """Clean up after tests"""
        self.patcher.stop()
        self.app_context.pop()
    
    def test_find_paths(self):
        """Test the GET /graph/paths endpoint"""
        # Configure find_paths return value
        paths = [
            [
                {"id": "entity1", "label": "Entity 1", "type": "concept", "relationship_to_next": "related_to"},
                {"id": "entity2", "label": "Entity 2", "type": "concept"}
            ]
        ]
        self.mock_query_engine.find_paths.return_value = paths
        
        # Make request to endpoint
        response = self.client.get('/api/graph/paths?source_id=entity1&target_id=entity2&max_length=2')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['paths'], paths)
        self.mock_query_engine.find_paths.assert_called_once_with("entity1", "entity2", 2)
    
    def test_find_paths_missing_parameters(self):
        """Test the GET /graph/paths endpoint with missing parameters"""
        # Missing target_id
        response = self.client.get('/api/graph/paths?source_id=entity1')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Source and target entity IDs are required")
    
    def test_find_paths_source_not_found(self):
        """Test the GET /graph/paths endpoint with non-existent source entity"""
        # Make request with invalid source_id
        response = self.client.get('/api/graph/paths?source_id=invalid_id&target_id=entity2')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Source entity 'invalid_id' not found")
    
    def test_find_paths_target_not_found(self):
        """Test the GET /graph/paths endpoint with non-existent target entity"""
        # Make request with invalid target_id
        response = self.client.get('/api/graph/paths?source_id=entity1&target_id=invalid_id')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Target entity 'invalid_id' not found")
    
    def test_get_related(self):
        """Test the GET /graph/related/{entity_id} endpoint"""
        # Configure get_related_concepts return value
        related_concepts = {
            "related_to": [
                {"id": "entity2", "label": "Entity 2", "type": "concept", "direction": "outgoing"}
            ],
            "inverse_part_of": [
                {"id": "entity3", "label": "Entity 3", "type": "concept", "direction": "incoming"}
            ]
        }
        self.mock_query_engine.get_related_concepts.return_value = related_concepts
        
        # Make request to endpoint
        response = self.client.get('/api/graph/related/entity1?relationship_types=related_to,part_of')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['entity']['id'], "entity1")
        self.assertEqual(data['entity']['label'], "Entity 1")
        self.assertEqual(data['entity']['type'], "concept")
        self.assertEqual(data['related'], related_concepts)
        
        # Check that get_related_concepts was called with the correct parameters
        self.mock_query_engine.get_related_concepts.assert_called_once_with("entity1", ["related_to", "part_of"])
    
    def test_get_related_entity_not_found(self):
        """Test the GET /graph/related/{entity_id} endpoint with non-existent entity"""
        # Make request with invalid entity_id
        response = self.client.get('/api/graph/related/invalid_id')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Entity 'invalid_id' not found")
    
    def test_get_central_entities(self):
        """Test the GET /graph/central endpoint"""
        # Configure get_central_entities return value
        central_entities = [
            {"id": "entity1", "label": "Entity 1", "type": "concept", "centrality": 0.8, "connections": 15},
            {"id": "entity2", "label": "Entity 2", "type": "concept", "centrality": 0.6, "connections": 10}
        ]
        self.mock_query_engine.get_central_entities.return_value = central_entities
        
        # Make request to endpoint
        response = self.client.get('/api/graph/central?count=5&type=concept')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['entities'], central_entities)
        
        # Check that get_central_entities was called with the correct parameters
        self.mock_query_engine.get_central_entities.assert_called_once_with(5)
    
    def test_get_entity_types(self):
        """Test the GET /graph/entity-types endpoint"""
        # Configure get_entity_types return value
        entity_types = {
            "concept": 15,
            "person": 10,
            "category": 5
        }
        self.mock_query_engine.get_entity_types.return_value = entity_types
        
        # Make request to endpoint
        response = self.client.get('/api/graph/entity-types')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['types'], entity_types)
        self.mock_query_engine.get_entity_types.assert_called_once()
    
    def test_get_relationship_types(self):
        """Test the GET /graph/relationship-types endpoint"""
        # Configure get_relationship_types return value
        relationship_types = {
            "related_to": 20,
            "contains": 15,
            "part_of": 10
        }
        self.mock_query_engine.get_relationship_types.return_value = relationship_types
        
        # Make request to endpoint
        response = self.client.get('/api/graph/relationship-types')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['types'], relationship_types)
        self.mock_query_engine.get_relationship_types.assert_called_once()
    
    def test_get_graph_stats(self):
        """Test the GET /graph/stats endpoint"""
        # Configure generate_ontology_summary return value
        summary = {
            "node_count": 30,
            "edge_count": 50,
            "entity_types": {"concept": 20, "person": 10},
            "relationship_types": {"related_to": 30, "contains": 20},
            "central_entities": [
                {"id": "entity1", "label": "Entity 1", "type": "concept", "centrality": 0.8, "connections": 15}
            ],
            "sections": 5,
            "subsections": 15
        }
        self.mock_query_engine.generate_ontology_summary.return_value = summary
        
        # Make request to endpoint
        response = self.client.get('/api/graph/stats')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['stats'], summary)
        self.mock_query_engine.generate_ontology_summary.assert_called_once()
    
    def test_no_ontology_data(self):
        """Test endpoints when no ontology data is loaded"""
        # Set query_engine to None to simulate no data loaded
        self.patcher.stop()
        
        # Patch load_query_engine to return False
        with patch('app.routes.main.load_query_engine', return_value=False):
            with patch('app.routes.main.query_engine', None):
                # Test one of the endpoints
                response = self.client.get('/api/graph/central')
                
                # Check response
                self.assertEqual(response.status_code, 404)
                data = json.loads(response.data)
                self.assertFalse(data['success'])
                self.assertIn('error', data)
                self.assertEqual(data['error'], "No ontology data loaded")
        
        # Restart the original patcher for other tests
        self.mock_api_query_engine = self.patcher.start()


if __name__ == '__main__':
    unittest.main()