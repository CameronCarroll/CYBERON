import os
import json
import pytest
import tempfile
import shutil
from flask import Flask, current_app
from app import create_app
from app.models.query_engine import CyberneticsQueryEngine
import app.routes.main as main_module
import datetime
import time
import uuid

# Mark all tests in this module with the 'integration' marker
pytestmark = pytest.mark.integration

class TestAPIIntegration:
    @pytest.fixture(autouse=True)
    def setup_app(self):
        """Set up the test application with a real database"""
        # Create a temporary directory for test data
        self.test_data_dir = tempfile.mkdtemp()
        self.test_upload_dir = tempfile.mkdtemp()
        
        # Configure the app for testing
        self.app = create_app(test_config={
            'TESTING': True,
            'DATA_FOLDER': self.test_data_dir,
            'UPLOAD_FOLDER': self.test_upload_dir
        })
        
        # Create a test client
        self.client = self.app.test_client()
        
        # Create an application context
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create a sample data file
        self.create_test_data()
        
        # Load the query engine with the test data
        main_module.load_query_engine()
        
        # Return the setup object
        yield
        
        # Clean up after the test
        self.app_context.pop()
        shutil.rmtree(self.test_data_dir)
        shutil.rmtree(self.test_upload_dir)
    
    def create_test_data(self):
        """Create initial test data for the knowledge graph"""
        # Create a simple knowledge graph with a few entities
        data_file = os.path.join(self.test_data_dir, 'cybernetics_ontology.json')
        
        # Create initial data structure
        data = {
            "metadata": {
                "title": "Integration Test Knowledge Graph",
                "description": "Test data for API integration tests",
                "created_at": datetime.datetime.utcnow().isoformat() + "Z",
                "version": "1.0.0"
            },
            "entities": [],
            "relationships": [],
            "sections": []
        }
        
        # Write the initial data to the file
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def wait_for_persistence(self):
        """Small delay to ensure data is persisted"""
        time.sleep(0.1)
    
    def test_entity_crud_operations(self):
        """Test the complete entity CRUD cycle"""
        # 1. Create an entity
        entity_data = {
            "label": "Test Entity 1",
            "type": "concept",
            "description": "Test entity for integration testing",
            "external_url": "https://example.com/test",
            "attributes": {
                "test_attr": "test_value"
            }
        }
        
        response = self.client.post(
            '/api/entities',
            json=entity_data,
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        created_entity = data['entity']
        entity_id = created_entity['id']
        
        # Allow time for persistence
        self.wait_for_persistence()
        
        # 2. Get the entity
        response = self.client.get(f'/api/entities/{entity_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['entity']['id'] == entity_id
        assert data['entity']['attributes']['label'] == "Test Entity 1"
        
        # 3. Update the entity
        update_data = {
            "label": "Updated Test Entity",
            "description": "Updated description"
        }
        
        response = self.client.put(
            f'/api/entities/{entity_id}',
            json=update_data,
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['entity']['attributes']['label'] == "Updated Test Entity"
        
        self.wait_for_persistence()
        
        # 4. Get the updated entity
        response = self.client.get(f'/api/entities/{entity_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['entity']['attributes']['label'] == "Updated Test Entity"
        
        # 5. Delete the entity
        response = self.client.delete(f'/api/entities/{entity_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        self.wait_for_persistence()
        
        # 6. Verify entity is deleted
        response = self.client.get(f'/api/entities/{entity_id}')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_relationship_crud_operations(self):
        """Test the complete relationship CRUD cycle"""
        # 1. Create two entities first
        entity1_data = {
            "label": "Source Entity",
            "type": "concept",
            "description": "Source entity for relationship testing"
        }
        
        entity2_data = {
            "label": "Target Entity",
            "type": "concept",
            "description": "Target entity for relationship testing"
        }
        
        # Create the first entity
        response = self.client.post(
            '/api/entities',
            json=entity1_data,
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        source_id = data['entity']['id']
        
        # Create the second entity
        response = self.client.post(
            '/api/entities',
            json=entity2_data,
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        target_id = data['entity']['id']
        
        self.wait_for_persistence()
        
        # 2. Create a relationship
        relationship_data = {
            "source_id": source_id,
            "target_id": target_id,
            "relationship_type": "related_to",
            "attributes": {
                "strength": "strong",
                "notes": "Test relationship"
            }
        }
        
        response = self.client.post(
            '/api/relationships',
            json=relationship_data,
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        relationship_id = data['relationship']['id']
        
        self.wait_for_persistence()
        
        # 3. Get the relationship
        response = self.client.get(f'/api/relationships/{relationship_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['relationship']['id'] == relationship_id
        assert data['relationship']['source_id'] == source_id
        assert data['relationship']['target_id'] == target_id
        assert data['relationship']['relationship_type'] == "related_to"
        
        # 4. Update the relationship
        update_data = {
            "relationship_type": "depends_on",
            "attributes": {
                "strength": "critical"
            }
        }
        
        response = self.client.put(
            f'/api/relationships/{relationship_id}',
            json=update_data,
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['relationship']['relationship_type'] == "depends_on"
        
        self.wait_for_persistence()
        
        # 5. Get the updated relationship
        response = self.client.get(f'/api/relationships/{relationship_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['relationship']['relationship_type'] == "depends_on"
        
        # 6. Delete the relationship
        response = self.client.delete(f'/api/relationships/{relationship_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        self.wait_for_persistence()
        
        # 7. Verify relationship is deleted
        response = self.client.get(f'/api/relationships/{relationship_id}')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        
        # 8. Clean up entities
        self.client.delete(f'/api/entities/{source_id}')
        self.client.delete(f'/api/entities/{target_id}')
    
    def test_entity_relationship_constraints(self):
        """Test entity deletion constraints with relationships"""
        # 1. Create two entities
        entity1_data = {"label": "Source Entity", "type": "concept", "description": "Source"}
        entity2_data = {"label": "Target Entity", "type": "concept", "description": "Target"}
        
        # Create the entities
        response = self.client.post('/api/entities', json=entity1_data, content_type='application/json')
        source_id = json.loads(response.data)['entity']['id']
        
        response = self.client.post('/api/entities', json=entity2_data, content_type='application/json')
        target_id = json.loads(response.data)['entity']['id']
        
        # 2. Create a relationship
        relationship_data = {
            "source_id": source_id,
            "target_id": target_id,
            "relationship_type": "related_to"
        }
        
        response = self.client.post('/api/relationships', json=relationship_data, content_type='application/json')
        assert response.status_code == 201
        
        self.wait_for_persistence()
        
        # 3. Try to delete source entity without cascade (should fail)
        response = self.client.delete(f'/api/entities/{source_id}')
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['success'] is False
        
        # 4. Delete with cascade=true
        response = self.client.delete(f'/api/entities/{source_id}?cascade=true')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['relationships_removed'] >= 1
        
        self.wait_for_persistence()
        
        # 5. Verify relationship is deleted
        response = self.client.get(f'/api/entities/{source_id}')
        assert response.status_code == 404
        
        # 6. Clean up target entity
        self.client.delete(f'/api/entities/{target_id}')
    
    def test_graph_operations(self):
        """Test graph operations with a simple network"""
        # 1. Create a small network of entities and relationships
        entities = [
            {"label": "Entity A", "type": "concept", "description": "Central node"},
            {"label": "Entity B", "type": "concept", "description": "Connected to A"},
            {"label": "Entity C", "type": "concept", "description": "Connected to A"},
            {"label": "Entity D", "type": "concept", "description": "Connected to B and C"}
        ]
        
        # Create entities
        entity_ids = []
        for entity_data in entities:
            response = self.client.post('/api/entities', json=entity_data, content_type='application/json')
            assert response.status_code == 201
            entity_ids.append(json.loads(response.data)['entity']['id'])
        
        # Create relationships: A->B, A->C, B->D, C->D
        relationships = [
            {"source_id": entity_ids[0], "target_id": entity_ids[1], "relationship_type": "connects_to"},
            {"source_id": entity_ids[0], "target_id": entity_ids[2], "relationship_type": "connects_to"},
            {"source_id": entity_ids[1], "target_id": entity_ids[3], "relationship_type": "depends_on"},
            {"source_id": entity_ids[2], "target_id": entity_ids[3], "relationship_type": "depends_on"}
        ]
        
        for rel_data in relationships:
            response = self.client.post('/api/relationships', json=rel_data, content_type='application/json')
            assert response.status_code == 201
        
        self.wait_for_persistence()
        
        # 2. Test path finding from A to D
        response = self.client.get(f'/api/graph/paths?source_id={entity_ids[0]}&target_id={entity_ids[3]}&max_length=3')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['paths']) >= 2  # Should find at least 2 paths
        
        # 3. Test related entities for A
        response = self.client.get(f'/api/graph/related/{entity_ids[0]}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'connects_to' in data['related']
        assert len(data['related']['connects_to']) == 2
        
        # 4. Test central entities
        response = self.client.get('/api/graph/central?count=4')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['entities']) <= 4
        
        # 5. Test entity and relationship types
        response = self.client.get('/api/graph/entity-types')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'concept' in data['types']
        assert data['types']['concept'] >= 4
        
        response = self.client.get('/api/graph/relationship-types')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'connects_to' in data['types']
        assert 'depends_on' in data['types']
        
        # 6. Test graph statistics
        response = self.client.get('/api/graph/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['stats']['node_count'] >= 4
        assert data['stats']['edge_count'] >= 4
        
        # 7. Clean up
        for entity_id in entity_ids:
            self.client.delete(f'/api/entities/{entity_id}?cascade=true')
    
    def test_listing_and_filtering(self):
        """Test entity and relationship listing with filters"""
        # 1. Create entities of different types
        entity_types = ["concept", "person", "category", "domain"]
        entity_ids_by_type = {}
        
        for entity_type in entity_types:
            entity_ids_by_type[entity_type] = []
            for i in range(3):  # Create 3 of each type
                entity_data = {
                    "label": f"{entity_type.capitalize()} {i+1}",
                    "type": entity_type,
                    "description": f"Test {entity_type} {i+1} for filtering"
                }
                
                response = self.client.post('/api/entities', json=entity_data, content_type='application/json')
                assert response.status_code == 201
                entity_ids_by_type[entity_type].append(json.loads(response.data)['entity']['id'])
        
        self.wait_for_persistence()
        
        # 2. Test filtering by type
        for entity_type in entity_types:
            response = self.client.get(f'/api/entities?type={entity_type}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert len(data['entities']) == 3
            for entity in data['entities']:
                assert entity['type'] == entity_type
        
        # 3. Test pagination
        response = self.client.get('/api/entities?limit=5&offset=0')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['entities']) == 5
        assert data['pagination']['limit'] == 5
        assert data['pagination']['offset'] == 0
        assert data['pagination']['next_offset'] == 5
        
        # 4. Test sorting
        response = self.client.get('/api/entities?sort=label&order=asc')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        labels = [entity['label'] for entity in data['entities']]
        assert sorted(labels) == labels
        
        # 5. Test search query
        response = self.client.get('/api/entities?q=Category')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        for entity in data['entities']:
            assert "Category" in entity['label'] or "category" in entity.get('description', "").lower()
        
        # 6. Create some relationships between entities
        for source_type in entity_types:
            for target_type in entity_types:
                if source_type != target_type:
                    rel_data = {
                        "source_id": entity_ids_by_type[source_type][0],
                        "target_id": entity_ids_by_type[target_type][0],
                        "relationship_type": f"{source_type}_to_{target_type}"
                    }
                    response = self.client.post('/api/relationships', json=rel_data, content_type='application/json')
                    assert response.status_code == 201
        
        self.wait_for_persistence()
        
        # 7. Test filtering relationships by type
        response = self.client.get('/api/relationships?type=concept_to_person')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        for rel in data['relationships']:
            assert rel['relationship_type'] == 'concept_to_person'
        
        # 8. Test filtering relationships by source
        source_id = entity_ids_by_type['concept'][0]
        response = self.client.get(f'/api/relationships?source_id={source_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        for rel in data['relationships']:
            assert rel['source_id'] == source_id
        
        # 9. Test filtering relationships by entity (as either source or target)
        entity_id = entity_ids_by_type['person'][0]
        response = self.client.get(f'/api/relationships?entity_id={entity_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        for rel in data['relationships']:
            assert rel['source_id'] == entity_id or rel['target_id'] == entity_id
        
        # 10. Clean up all entities
        for type_ids in entity_ids_by_type.values():
            for entity_id in type_ids:
                self.client.delete(f'/api/entities/{entity_id}?cascade=true')
    
    def test_data_persistence(self):
        """Test that data changes are persisted to disk"""
        # 1. Create an entity
        entity_data = {
            "label": "Persistence Test Entity",
            "type": "concept",
            "description": "Testing data persistence"
        }
        
        response = self.client.post('/api/entities', json=entity_data, content_type='application/json')
        assert response.status_code == 201
        entity_id = json.loads(response.data)['entity']['id']
        
        self.wait_for_persistence()
        
        # 2. Force query engine to reload data from disk
        with self.app.app_context():
            # Store the current query_engine
            original_query_engine = main_module.query_engine
            
            # Set query_engine to None to force a reload
            main_module.query_engine = None
            
            # Reload the query engine from disk
            success = main_module.load_query_engine()
            assert success is True
            
            # Check that the entity exists in the reloaded data
            reloaded_entity = main_module.query_engine.query_entity(entity_id)
            assert "error" not in reloaded_entity
            assert reloaded_entity['attributes']['label'] == "Persistence Test Entity"
            
            # Restore the original query_engine
            main_module.query_engine = original_query_engine
        
        # 3. Clean up
        self.client.delete(f'/api/entities/{entity_id}')
    
    def test_error_handling(self):
        """Test API error handling"""
        # 1. Test entity not found
        response = self.client.get('/api/entities/nonexistent_id')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
        
        # 2. Test invalid entity creation (missing required field)
        invalid_data = {
            "label": "Invalid Entity"
            # Missing type field
        }
        
        response = self.client.post('/api/entities', json=invalid_data, content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
        
        # 3. Test relationship validation (non-existent source)
        invalid_rel = {
            "source_id": "nonexistent_id",
            "target_id": "also_nonexistent",
            "relationship_type": "test_relationship"
        }
        
        response = self.client.post('/api/relationships', json=invalid_rel, content_type='application/json')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data