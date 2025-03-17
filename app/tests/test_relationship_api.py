import json
import unittest
import pytest
from unittest.mock import patch, MagicMock
import datetime

from app import create_app
from app.models.query_engine import CyberneticsQueryEngine

# Mark all tests in this module with the 'api' marker
pytestmark = pytest.mark.api


class TestRelationshipAPI(unittest.TestCase):
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
        
        # Configure entity responses for testing
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
        
        # Sample relationship data for creating
        self.relationship_data = {
            "source_id": "entity1",
            "target_id": "entity2",
            "relationship_type": "related_to",
            "attributes": {
                "key1": "value1",
                "key2": "value2"
            }
        }
        
        # Sample relationship response
        self.relationship_response = {
            "id": "rel_12345",
            "source_id": "entity1",
            "source_label": "Entity 1",
            "target_id": "entity2",
            "target_label": "Entity 2",
            "relationship_type": "related_to",
            "attributes": {
                "key1": "value1",
                "key2": "value2"
            },
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        
        # Configure mock methods
        self.mock_query_engine.query_entity.side_effect = lambda id: self.entity1 if id == "entity1" else self.entity2
        self.mock_query_engine.create_relationship.return_value = self.relationship_response
        self.mock_query_engine.save_changes.return_value = True
    
    def tearDown(self):
        """Clean up after tests"""
        self.patcher.stop()
        self.app_context.pop()
    
    def test_create_relationship(self):
        """Test the POST /relationships endpoint"""
        # Make request to endpoint
        response = self.client.post(
            '/api/relationships',
            json=self.relationship_data,
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['relationship'], self.relationship_response)
        self.mock_query_engine.create_relationship.assert_called_once_with(self.relationship_data)
        self.mock_query_engine.save_changes.assert_called_once()
    
    def test_create_relationship_validation_error(self):
        """Test validation error when creating relationship"""
        # Invalid data missing required fields
        invalid_data = {
            "source_id": "entity1"
            # Missing target_id and relationship_type
        }
        
        response = self.client.post(
            '/api/relationships',
            json=invalid_data,
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        # The specific error will depend on which validation happens first
        self.assertTrue("Target entity ID is required" in data['error'] or 
                      "Relationship type is required" in data['error'])
    
    def test_create_relationship_source_not_found(self):
        """Test creating relationship with non-existent source entity"""
        # Configure query_entity to return error for source
        self.mock_query_engine.query_entity.side_effect = lambda id: {"error": f"Entity '{id}' not found"} if id == "invalid_id" else self.entity2
        
        # Data with invalid source_id
        invalid_data = {
            "source_id": "invalid_id",
            "target_id": "entity2",
            "relationship_type": "related_to"
        }
        
        response = self.client.post(
            '/api/relationships',
            json=invalid_data,
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Source entity 'invalid_id' not found")
    
    def test_create_relationship_target_not_found(self):
        """Test creating relationship with non-existent target entity"""
        # Configure query_entity to return error for target
        self.mock_query_engine.query_entity.side_effect = lambda id: self.entity1 if id == "entity1" else {"error": f"Entity '{id}' not found"}
        
        # Data with invalid target_id
        invalid_data = {
            "source_id": "entity1",
            "target_id": "invalid_id",
            "relationship_type": "related_to"
        }
        
        response = self.client.post(
            '/api/relationships',
            json=invalid_data,
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Target entity 'invalid_id' not found")
    
    def test_get_relationship(self):
        """Test the GET /relationships/{relationship_id} endpoint"""
        # Configure get_relationship return value
        relationship_detail = {
            "id": "rel_12345",
            "source_id": "entity1",
            "source_label": "Entity 1",
            "source_type": "concept",
            "target_id": "entity2",
            "target_label": "Entity 2",
            "target_type": "concept",
            "relationship_type": "related_to",
            "attributes": {
                "key1": "value1",
                "key2": "value2"
            },
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        self.mock_query_engine.get_relationship.return_value = relationship_detail
        
        # Make request to endpoint
        response = self.client.get('/api/relationships/rel_12345')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['relationship'], relationship_detail)
        self.mock_query_engine.get_relationship.assert_called_once_with("rel_12345")
    
    def test_get_relationship_not_found(self):
        """Test getting a non-existent relationship"""
        # Configure get_relationship to return None
        self.mock_query_engine.get_relationship.return_value = None
        
        # Make request to endpoint
        response = self.client.get('/api/relationships/not_found')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Relationship 'not_found' not found")
    
    def test_update_relationship(self):
        """Test the PUT /relationships/{relationship_id} endpoint"""
        # Data to update
        update_data = {
            "relationship_type": "depends_on",
            "attributes": {
                "key1": "updated_value",
                "key3": "new_value"
            }
        }
        
        # Configure update_relationship return value
        updated_relationship = {
            "id": "rel_12345",
            "source_id": "entity1",
            "target_id": "entity2",
            "relationship_type": "depends_on",
            "attributes": {
                "key1": "updated_value",
                "key2": "value2",
                "key3": "new_value"
            },
            "updated_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        self.mock_query_engine.update_relationship.return_value = updated_relationship
        
        # Make request to endpoint
        response = self.client.put(
            '/api/relationships/rel_12345',
            json=update_data,
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['relationship'], updated_relationship)
        self.mock_query_engine.update_relationship.assert_called_once_with("rel_12345", update_data)
        self.mock_query_engine.save_changes.assert_called_once()
    
    def test_update_relationship_not_found(self):
        """Test updating a non-existent relationship"""
        # Configure update_relationship to return None
        self.mock_query_engine.update_relationship.return_value = None
        
        # Make request to endpoint
        response = self.client.put(
            '/api/relationships/not_found',
            json={"relationship_type": "updated_type"},
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Relationship 'not_found' not found")
    
    def test_delete_relationship(self):
        """Test the DELETE /relationships/{relationship_id} endpoint"""
        # Configure delete_relationship to return True
        self.mock_query_engine.delete_relationship.return_value = True
        
        # Make request to endpoint
        response = self.client.delete('/api/relationships/rel_12345')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], "Relationship deleted successfully")
        self.mock_query_engine.delete_relationship.assert_called_once_with("rel_12345")
        self.mock_query_engine.save_changes.assert_called_once()
    
    def test_delete_relationship_not_found(self):
        """Test deleting a non-existent relationship"""
        # Configure delete_relationship to return False
        self.mock_query_engine.delete_relationship.return_value = False
        
        # Make request to endpoint
        response = self.client.delete('/api/relationships/not_found')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Relationship 'not_found' not found")
    
    def test_list_relationships(self):
        """Test the GET /relationships endpoint"""
        # Configure list_relationships return value
        relationships_list = {
            "relationships": [
                {
                    "id": "rel_1",
                    "source_id": "entity1",
                    "source_label": "Entity 1",
                    "target_id": "entity2",
                    "target_label": "Entity 2",
                    "relationship_type": "related_to",
                    "created_at": "2023-01-01T12:00:00Z"
                },
                {
                    "id": "rel_2",
                    "source_id": "entity2",
                    "source_label": "Entity 2",
                    "target_id": "entity3",
                    "target_label": "Entity 3",
                    "relationship_type": "depends_on",
                    "created_at": "2023-01-02T12:00:00Z"
                }
            ],
            "total": 2
        }
        self.mock_query_engine.list_relationships.return_value = relationships_list
        
        # Make request to endpoint
        response = self.client.get('/api/relationships?source_id=entity1&type=related_to&limit=10&offset=0')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['relationships'], relationships_list['relationships'])
        self.assertEqual(data['pagination']['total'], 2)
        
        # Check that list_relationships was called with the correct parameters
        self.mock_query_engine.list_relationships.assert_called_once_with(
            source_id='entity1',
            target_id=None,
            entity_id=None,
            relationship_type='related_to',
            limit=10,
            offset=0,
            sort='created_at',
            order='desc'
        )
    
    def test_list_relationships_by_entity(self):
        """Test the GET /relationships endpoint with entity_id filter"""
        # Configure list_relationships return value
        relationships_list = {
            "relationships": [
                {
                    "id": "rel_1",
                    "source_id": "entity1",
                    "source_label": "Entity 1",
                    "target_id": "entity2",
                    "target_label": "Entity 2",
                    "relationship_type": "related_to",
                    "created_at": "2023-01-01T12:00:00Z"
                }
            ],
            "total": 1
        }
        self.mock_query_engine.list_relationships.return_value = relationships_list
        
        # Make request to endpoint
        response = self.client.get('/api/relationships?entity_id=entity1')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['relationships'], relationships_list['relationships'])
        
        # Check that list_relationships was called with the correct parameters
        self.mock_query_engine.list_relationships.assert_called_once_with(
            source_id=None,
            target_id=None,
            entity_id='entity1',
            relationship_type=None,
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
                response = self.client.get('/api/relationships/rel_12345')
                
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