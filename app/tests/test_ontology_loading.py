import unittest
import pytest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, mock_open, MagicMock
from app import create_app
from app.routes.main import load_query_engine
from app.models.query_engine import CyberneticsQueryEngine

# Mark all tests in this module with the 'data_loading' marker
pytestmark = pytest.mark.data_loading

# Sample data for testing
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
            {"id": "node1", "label": "First Node", "type": "concept"}
        ],
        "edges": [
            {"source": "node1", "target": "node2", "label": "related_to"}
        ]
    }
}

class TestOntologyLoading(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = create_app(testing=True)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.data_file = os.path.join(self.temp_dir, 'cybernetics_ontology.json')
        
        # Write sample data to the file
        with open(self.data_file, 'w') as f:
            json.dump(SAMPLE_DATA, f)
        
        # Override the app's data folder setting
        self.app.config['DATA_FOLDER'] = self.temp_dir
    
    def tearDown(self):
        """Clean up after tests"""
        self.app_context.pop()
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_load_query_engine_success(self):
        """Test loading the query engine successfully"""
        # Patch CyberneticsQueryEngine to avoid actually loading data
        with patch('app.routes.main.CyberneticsQueryEngine') as mock_engine_class:
            # Create a mock instance to be returned by the constructor
            mock_engine = MagicMock()
            mock_engine_class.return_value = mock_engine
            
            # Provide mock graph for the instance
            mock_graph = MagicMock()
            mock_graph.number_of_nodes.return_value = 5
            mock_graph.number_of_edges.return_value = 10
            mock_engine.graph = mock_graph
            
            # Call the function
            import app.routes.main as main_module
            main_module.query_engine = None  # Reset to None for the test
            result = load_query_engine()
            
            # Verify result and that engine was created with correct path
            self.assertTrue(result)
            mock_engine_class.assert_called_once_with(self.data_file)
            
            # Verify global query_engine was set
            self.assertEqual(main_module.query_engine, mock_engine)
    
    def test_load_query_engine_file_not_found(self):
        """Test loading when the data file doesn't exist"""
        # Remove the data file
        os.remove(self.data_file)
        
        # Call the function
        import app.routes.main as main_module
        main_module.query_engine = None  # Reset to None for the test
        result = load_query_engine()
        
        # Verify result
        self.assertFalse(result)
        self.assertIsNone(main_module.query_engine)
    
    def test_integration_data_loading(self):
        """Integration test for actual data loading"""
        # Reset the query engine
        import app.routes.main as main_module
        main_module.query_engine = None
        
        # Call the function (using the real implementation)
        result = load_query_engine()
        
        # Verify result
        self.assertTrue(result)
        self.assertIsNotNone(main_module.query_engine)
        self.assertIsInstance(main_module.query_engine, CyberneticsQueryEngine)
        
        # Verify the engine contains the expected data
        engine = main_module.query_engine
        self.assertEqual(engine.data_source, self.data_file)
        self.assertEqual(len(engine.structured_ontology), 1)
        self.assertIn("1", engine.structured_ontology)
        self.assertGreaterEqual(engine.graph.number_of_nodes(), 1)
    
    def test_load_in_visualization_route(self):
        """Test that the visualization route tries to load data"""
        # Reset the query engine
        import app.routes.main as main_module
        main_module.query_engine = None
        
        # Create a test client
        client = self.app.test_client()
        
        # Mock the load_query_engine function to verify it's called
        with patch('app.routes.main.load_query_engine') as mock_load:
            # Set up the mock to set a query engine
            mock_engine = MagicMock(spec=CyberneticsQueryEngine)
            mock_graph = MagicMock()
            mock_engine.graph = mock_graph
            mock_engine.data_source = self.data_file
            
            def set_engine(*args, **kwargs):
                main_module.query_engine = mock_engine
                return True
            
            mock_load.side_effect = set_engine
            
            # Also mock generate_ontology_summary to avoid errors
            mock_engine.generate_ontology_summary.return_value = {
                "node_count": 5,
                "edge_count": 10,
                "entity_types": {},
                "relationship_types": {},
                "central_entities": []
            }
            
            # Make a request to the ontology route
            response = client.get('/ontology')
            
            # Verify load_query_engine was called
            mock_load.assert_called_once()
            
            # Verify the response is successful (not an error page)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Ontology Visualization', response.data)
            self.assertNotIn(b'No ontology data loaded', response.data)
            
            # Verify generate_ontology_summary was called
            mock_engine.generate_ontology_summary.assert_called_once()
    
    def test_auto_load_before_request(self):
        """Test that the app tries to load data before handling a request"""
        # Reset the query engine
        import app.routes.main as main_module
        main_module.query_engine = None
        
        # Create a test client
        client = self.app.test_client()
        
        # Mock the load_query_engine function to verify it's called
        with patch('app.routes.main.load_query_engine') as mock_load:
            mock_load.return_value = True
            
            # Make a request to the index route
            response = client.get('/')
            
            # Verify load_query_engine was called
            mock_load.assert_called_once()

if __name__ == '__main__':
    unittest.main()