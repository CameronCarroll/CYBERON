import json
import unittest
import pytest
from unittest.mock import patch, MagicMock
import datetime

from app import create_app
from app.models.query_engine import CyberneticsQueryEngine

# Mark all tests in this module with the 'api' marker
pytestmark = pytest.mark.api


class TestEntityAPI(unittest.TestCase):
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
        
        # Sample entity data
        self.entity_data = {
            "label": "Test Entity",
            "type": "concept",
            "description": "This is a test entity",
            "external_url": "https://example.com",
            "attributes": {
                "key1": "value1",
                "key2": "value2"
            }
        }
        
        # Sample entity response
        self.entity_response = {
            "id": "test_entity",
            "attributes": {
                "label": "Test Entity",
                "type": "concept",
                "description": "This is a test entity",
                "external_url": "https://example.com",
                "key1": "value1",
                "key2": "value2",
                "created_at": datetime.datetime.utcnow().isoformat() + "Z"
            },
            "incoming": [],
            "outgoing": []
        }
        
        # Configure mock create_entity return value
        self.mock_query_engine.create_entity.return_value = self.entity_response
        
        # Configure mock save_changes return value
        self.mock_query_engine.save_changes.return_value = True
    
    def tearDown(self):
        """Clean up after tests"""
        self.patcher.stop()
        self.app_context.pop()
    
    def test_create_entity(self):
        """Test the POST /entities endpoint"""
        # Make request to endpoint
        response = self.client.post(
            '/api/entities',
            json=self.entity_data,
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['entity'], self.entity_response)
        self.mock_query_engine.create_entity.assert_called_once_with(self.entity_data)
        self.mock_query_engine.save_changes.assert_called_once()
    
    def test_create_entity_validation_error(self):
        """Test validation error when creating entity"""
        # Attempt to create entity with missing required fields
        invalid_data = {
            "label": "Test Entity"  # Missing type field
        }
        
        response = self.client.post(
            '/api/entities',
            json=invalid_data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Entity type is required")
    
    def test_get_entity(self):
        """Test the GET /entities/{entity_id} endpoint"""
        # Configure mock query_entity return value
        self.mock_query_engine.query_entity.return_value = self.entity_response
        
        # Make request to endpoint
        response = self.client.get('/api/entities/test_entity')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['entity'], self.entity_response)
        self.mock_query_engine.query_entity.assert_called_once_with("test_entity")
    
    def test_get_entity_not_found(self):
        """Test getting a non-existent entity"""
        # Configure mock query_entity to return error
        self.mock_query_engine.query_entity.return_value = {"error": "Entity 'not_found' not found"}
        
        # Make request to endpoint
        response = self.client.get('/api/entities/not_found')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Entity 'not_found' not found")
    
    def test_update_entity(self):
        """Test the PUT /entities/{entity_id} endpoint"""
        # Data to update
        update_data = {
            "label": "Updated Entity",
            "description": "Updated description"
        }
        
        # Configure mock update_entity return value
        updated_entity = {
            "id": "test_entity",
            "attributes": {
                "label": "Updated Entity",
                "type": "concept",
                "description": "Updated description",
                "external_url": "https://example.com",
                "key1": "value1",
                "key2": "value2",
                "created_at": datetime.datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.datetime.utcnow().isoformat() + "Z"
            }
        }
        self.mock_query_engine.update_entity.return_value = updated_entity
        
        # Make request to endpoint
        response = self.client.put(
            '/api/entities/test_entity',
            json=update_data,
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['entity'], updated_entity)
        self.mock_query_engine.update_entity.assert_called_once_with("test_entity", update_data)
        self.mock_query_engine.save_changes.assert_called_once()
    
    def test_update_entity_not_found(self):
        """Test updating a non-existent entity"""
        # Configure mock update_entity to return None (not found)
        self.mock_query_engine.update_entity.return_value = None
        
        # Make request to endpoint
        response = self.client.put(
            '/api/entities/not_found',
            json={"label": "Updated Label"},
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Entity 'not_found' not found")
    
    def test_delete_entity(self):
        """Test the DELETE /entities/{entity_id} endpoint"""
        # Configure mock delete_entity return value
        self.mock_query_engine.delete_entity.return_value = {
            "success": True,
            "relationships_removed": 2
        }
        
        # Make request to endpoint
        response = self.client.delete('/api/entities/test_entity')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], "Entity deleted successfully")
        self.assertEqual(data['relationships_removed'], 2)
        self.mock_query_engine.delete_entity.assert_called_once_with("test_entity", False)
        self.mock_query_engine.save_changes.assert_called_once()
    
    def test_delete_entity_with_cascade(self):
        """Test the DELETE /entities/{entity_id} endpoint with cascade=true"""
        # Configure mock delete_entity return value
        self.mock_query_engine.delete_entity.return_value = {
            "success": True,
            "relationships_removed": 5
        }
        
        # Make request to endpoint
        response = self.client.delete('/api/entities/test_entity?cascade=true')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], "Entity deleted successfully")
        self.assertEqual(data['relationships_removed'], 5)
        self.mock_query_engine.delete_entity.assert_called_once_with("test_entity", True)
        self.mock_query_engine.save_changes.assert_called_once()
    
    def test_delete_entity_not_found(self):
        """Test deleting a non-existent entity"""
        # Configure mock delete_entity to indicate not found
        self.mock_query_engine.delete_entity.return_value = {
            "success": False,
            "not_found": True
        }
        
        # Make request to endpoint
        response = self.client.delete('/api/entities/not_found')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Entity 'not_found' not found")
    
    def test_delete_entity_with_relationships(self):
        """Test deleting an entity that has relationships without cascade"""
        # Configure mock delete_entity to indicate relationships exist
        self.mock_query_engine.delete_entity.return_value = {
            "success": False,
            "message": "Entity has relationships. Use cascade=true to delete them."
        }
        
        # Make request to endpoint
        response = self.client.delete('/api/entities/test_entity')
        
        # Check response
        self.assertEqual(response.status_code, 409)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Entity has relationships. Use cascade=true to delete them.")
    
    def test_list_entities(self):
        """Test the GET /entities endpoint"""
        # Configure mock list_entities return value
        entities_list = {
            "entities": [
                {
                    "id": "entity1",
                    "label": "Entity 1",
                    "type": "concept",
                    "description": "Description 1",
                    "created_at": "2023-01-01T12:00:00Z"
                },
                {
                    "id": "entity2",
                    "label": "Entity 2",
                    "type": "person",
                    "description": "Description 2",
                    "created_at": "2023-01-02T12:00:00Z"
                }
            ],
            "total": 2
        }
        self.mock_query_engine.list_entities.return_value = entities_list
        
        # Make request to endpoint
        response = self.client.get('/api/entities?type=concept&limit=10&offset=0&sort=label&order=asc')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['entities'], entities_list['entities'])
        self.assertEqual(data['pagination']['total'], 2)
        self.assertEqual(data['pagination']['offset'], 0)
        self.assertEqual(data['pagination']['limit'], 10)
        self.assertEqual(data['pagination']['next_offset'], None)  # None because total < limit
        
        # Check that list_entities was called with the correct parameters
        self.mock_query_engine.list_entities.assert_called_once_with(
            entity_type='concept',
            query=None,
            limit=10,
            offset=0,
            sort='label',
            order='asc'
        )
    
    def test_list_entities_with_search(self):
        """Test the GET /entities endpoint with search query"""
        # Configure mock list_entities return value
        entities_list = {
            "entities": [
                {
                    "id": "entity1",
                    "label": "Test Entity",
                    "type": "concept",
                    "description": "Contains test in description",
                    "created_at": "2023-01-01T12:00:00Z"
                }
            ],
            "total": 1
        }
        self.mock_query_engine.list_entities.return_value = entities_list
        
        # Make request to endpoint
        response = self.client.get('/api/entities?q=test')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['entities'], entities_list['entities'])
        
        # Check that list_entities was called with the correct parameters
        self.mock_query_engine.list_entities.assert_called_once_with(
            entity_type=None,
            query='test',
            limit=50,
            offset=0,
            sort='created_at',
            order='desc'
        )
    
    def test_no_ontology_data(self):
        """Test endpoints when no ontology data is loaded"""
        # Set query_engine to None to simulate no data loaded
        self.patcher.stop()
        
        # Patch load_query_engine to return False
        with patch('app.routes.main.load_query_engine', return_value=False):
            with patch('app.routes.main.query_engine', None):
                # Test one of the endpoints
                response = self.client.get('/api/entities/test_entity')
                
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