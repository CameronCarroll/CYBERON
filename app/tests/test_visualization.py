import unittest
import pytest
from unittest.mock import patch, MagicMock
import json
import os
from app import create_app
from app.models.query_engine import CyberneticsQueryEngine
import app.routes.main as main_module
import networkx as nx

# Mark all tests in this module with the 'visualization' marker
pytestmark = pytest.mark.visualization

class TestVisualizationRoutes(unittest.TestCase):
    def setUp(self):
        """Set up test client and app context"""
        self.app = create_app(testing=True)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Mock the query engine
        self.mock_query_engine = MagicMock(spec=CyberneticsQueryEngine)
        self.mock_graph = MagicMock(spec=nx.DiGraph)
        self.mock_query_engine.graph = self.mock_graph
        self.mock_query_engine.data_source = "test_source.json"
        
        # Configure common mock methods
        self.mock_graph.number_of_nodes.return_value = 10
        self.mock_graph.number_of_edges.return_value = 15
        
        # Create a sample ontology summary for the visualization route
        self.mock_summary = {
            "node_count": 10,
            "edge_count": 15,
            "entity_types": {"concept": 5, "person": 3, "theory": 2},
            "relationship_types": {"related_to": 8, "developed_by": 4, "evolved_into": 3},
            "central_entities": [
                {"id": "entity1", "label": "Entity 1", "type": "concept", "centrality": 0.8}
            ]
        }
        self.mock_query_engine.generate_ontology_summary.return_value = self.mock_summary
        
        # Save the original query_engine reference
        self.original_query_engine = main_module.query_engine
        
        # Replace with our mock
        main_module.query_engine = self.mock_query_engine
    
    def tearDown(self):
        """Clean up after tests"""
        # Restore original query_engine
        main_module.query_engine = self.original_query_engine
        self.app_context.pop()
    
    def test_ontology_route_success(self):
        """Test the /ontology visualization route when data is loaded"""
        # Make request to the ontology route
        response = self.client.get('/ontology')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Cybernetics Ontology Visualization', response.data)
        self.assertIn(b'Total: <span class="font-mono">10</span>', response.data)
        
        # Verify the mock was called
        self.mock_query_engine.generate_ontology_summary.assert_called_once()
    
    def test_ontology_route_no_data(self):
        """Test the /ontology route when no data is loaded"""
        # Set query_engine to None to simulate no data
        main_module.query_engine = None
        
        # Mock the load_query_engine function to return False (failed to load)
        with patch('app.routes.main.load_query_engine', return_value=False):
            # Make request to the ontology route
            response = self.client.get('/ontology')
            
            # Check response - should show error page
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'No ontology data loaded', response.data)
    
    def test_ontology_route_exception(self):
        """Test the /ontology route when an exception occurs"""
        # Configure generate_ontology_summary to raise an exception
        self.mock_query_engine.generate_ontology_summary.side_effect = Exception("Test error")
        
        # Make request to the ontology route
        response = self.client.get('/ontology')
        
        # Check response - should show error page with the exception message
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Error generating visualization', response.data)
        self.assertIn(b'Test error', response.data)
    
    def test_explore_route_success(self):
        """Test the /explore route when data is loaded"""
        # Make request to the explore route
        response = self.client.get('/explore')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        # This would check for content in the explore.html template
    
    def test_explore_route_no_data(self):
        """Test the /explore route when no data is loaded"""
        # Set query_engine to None to simulate no data
        main_module.query_engine = None
        
        # Mock the load_query_engine function to return False (failed to load)
        with patch('app.routes.main.load_query_engine', return_value=False):
            # Make request to the explore route
            response = self.client.get('/explore')
            
            # Check response - should show error page
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'No ontology data loaded', response.data)
    
    def test_data_loading_before_request(self):
        """Test that the app tries to load data before handling a request"""
        # Set query_engine to None
        main_module.query_engine = None
        
        # Mock the load_query_engine function 
        with patch('app.routes.main.load_query_engine') as mock_load:
            mock_load.return_value = True
            
            # Create a new mock engine for the load function to set
            new_mock_engine = MagicMock(spec=CyberneticsQueryEngine)
            
            # When load_query_engine is called, set the engine
            def set_engine(*args, **kwargs):
                main_module.query_engine = new_mock_engine
                return True
            
            mock_load.side_effect = set_engine
            
            # Make a request that should trigger the before_app_request handler
            response = self.client.get('/')
            
            # Verify load_query_engine was called
            mock_load.assert_called_once()
            
            # Verify the engine is now the new mock engine
            self.assertEqual(main_module.query_engine, new_mock_engine)

if __name__ == '__main__':
    unittest.main()