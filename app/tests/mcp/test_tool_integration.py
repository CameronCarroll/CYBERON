"""
Tests for the MCP tool functionality.

This module contains tests for the MCP tool handlers.
"""

import pytest
import json
from unittest.mock import patch, MagicMock

# Import handlers
from app.mcp.handlers.tools import (
    set_query_engine,
    list_tools_handler,
    get_tool_schema_handler,
    execute_tool_handler,
    register_default_tools,
    search_entities_tool,
    analyze_entity_tool,
    compare_entities_tool,
    find_central_entities_tool,
    summarize_ontology_tool
)

class TestToolHandlers:
    """Tests for the MCP tool handlers."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up the test environment."""
        # Register the default tools
        register_default_tools()
        
        # Create a mock query engine
        self.mock_query_engine = MagicMock()
        set_query_engine(self.mock_query_engine)
        
        # Configure mock for search
        mock_search_results = [
            {"id": "entity1", "label": "Entity 1", "type": "concept", "match_score": 0.9},
            {"id": "entity2", "label": "Entity 2", "type": "concept", "match_score": 0.7}
        ]
        self.mock_query_engine.search_entities.return_value = mock_search_results
        
        # Configure mock for entity
        mock_entity = {
            "id": "entity1",
            "attributes": {
                "label": "Entity 1",
                "type": "concept"
            },
            "incoming": [{"id": "rel1"}, {"id": "rel2"}],
            "outgoing": [{"id": "rel3"}]
        }
        self.mock_query_engine.query_entity.return_value = mock_entity
        
        # Configure mock for connections
        mock_connections = [
            {"entity": {"id": "entity2"}, "relationship": {"type": "related_to"}},
            {"entity": {"id": "entity3"}, "relationship": {"type": "part_of"}}
        ]
        self.mock_query_engine.find_connections.return_value = mock_connections
        
        # Configure mock for paths
        mock_paths = [
            [
                {"id": "entity1", "label": "Entity 1", "type": "concept"},
                {"id": "rel1", "type": "related_to"},
                {"id": "entity2", "label": "Entity 2", "type": "concept"}
            ]
        ]
        self.mock_query_engine.find_paths.return_value = mock_paths
        
        # Configure mock for entity types
        mock_entity_types = {"concept": 10, "person": 5, "system": 3}
        self.mock_query_engine.get_entity_types.return_value = mock_entity_types
        
        # Configure mock for relationship types
        mock_rel_types = {"related_to": 15, "part_of": 8, "influenced_by": 5}
        self.mock_query_engine.get_relationship_types.return_value = mock_rel_types
        
        # Configure mock for central entities
        mock_central_entities = [
            {"id": "entity1", "label": "Entity 1", "centrality": 0.9},
            {"id": "entity2", "label": "Entity 2", "centrality": 0.8},
            {"id": "entity3", "label": "Entity 3", "centrality": 0.7}
        ]
        self.mock_query_engine.get_central_entities.return_value = mock_central_entities
        
        # Set up a mock transport ID
        self.transport_id = "test-transport"
        
        yield
        
        # Clean up after test
        set_query_engine(None)
    
    def test_list_tools_handler(self):
        """Test the list_tools_handler function."""
        # Call the handler
        result = list_tools_handler({}, self.transport_id)
        
        # Verify result
        assert "tools" in result
        assert len(result["tools"]) > 0
        
        # Verify tool format
        for tool in result["tools"]:
            assert "name" in tool
            assert "description" in tool
            assert "schema" in tool
    
    def test_get_tool_schema_handler(self):
        """Test the get_tool_schema_handler function."""
        # Call the handler
        result = get_tool_schema_handler({"name": "cyberon.tools.search"}, self.transport_id)
        
        # Verify result
        assert "name" in result
        assert "schema" in result
        assert result["name"] == "cyberon.tools.search"
    
    def test_get_tool_schema_handler_not_found(self):
        """Test the get_tool_schema_handler function with non-existent tool."""
        # Call the handler
        result = get_tool_schema_handler({"name": "non_existent_tool"}, self.transport_id)
        
        # Verify result
        assert "error" in result
    
    def test_execute_tool_handler_search(self):
        """Test the execute_tool_handler function with search tool."""
        # Call the handler
        result = execute_tool_handler({
            "name": "cyberon.tools.search",
            "params": {
                "query": "test query",
                "limit": 5
            }
        }, self.transport_id)
        
        # Verify result
        assert "name" in result
        assert "timestamp" in result
        assert "result" in result
        assert result["name"] == "cyberon.tools.search"
        
        # Verify tool result
        tool_result = result["result"]
        assert "entities" in tool_result
        assert "query" in tool_result
        assert "total" in tool_result
        assert tool_result["entities"] == self.mock_query_engine.search_entities.return_value
        assert tool_result["query"] == "test query"
        assert tool_result["total"] == 2
        
        # Verify mock was called correctly
        self.mock_query_engine.search_entities.assert_called_with("test query", None)
    
    def test_execute_tool_handler_analyze_entity(self):
        """Test the execute_tool_handler function with analyze_entity tool."""
        # Call the handler
        result = execute_tool_handler({
            "name": "cyberon.tools.analyze_entity",
            "params": {
                "entity_id": "entity1"
            }
        }, self.transport_id)
        
        # Verify result
        assert "name" in result
        assert "timestamp" in result
        assert "result" in result
        assert result["name"] == "cyberon.tools.analyze_entity"
        
        # Verify tool result
        tool_result = result["result"]
        assert "entity" in tool_result
        assert "stats" in tool_result
        assert tool_result["entity"]["id"] == "entity1"
        assert tool_result["entity"]["label"] == "Entity 1"
        assert tool_result["stats"]["incoming_relationships"] == 2
        assert tool_result["stats"]["outgoing_relationships"] == 1
        
        # Verify mocks were called correctly
        self.mock_query_engine.query_entity.assert_called_with("entity1")
        self.mock_query_engine.find_connections.assert_called_with("entity1", 1)
    
    def test_execute_tool_handler_not_found(self):
        """Test the execute_tool_handler function with non-existent tool."""
        # Call the handler
        result = execute_tool_handler({
            "name": "non_existent_tool",
            "params": {}
        }, self.transport_id)
        
        # Verify result
        assert "error" in result
    
    def test_search_entities_tool(self):
        """Test the search_entities_tool function."""
        # Call the tool directly
        result = search_entities_tool({
            "query": "test query",
            "limit": 5
        }, self.transport_id)
        
        # Verify result
        assert "entities" in result
        assert "query" in result
        assert "total" in result
        assert result["entities"] == self.mock_query_engine.search_entities.return_value
        assert result["query"] == "test query"
        
        # Verify mock was called correctly
        self.mock_query_engine.search_entities.assert_called_with("test query", None)
    
    def test_analyze_entity_tool(self):
        """Test the analyze_entity_tool function."""
        # Call the tool directly
        result = analyze_entity_tool({
            "entity_id": "entity1"
        }, self.transport_id)
        
        # Verify result
        assert "entity" in result
        assert "stats" in result
        assert result["entity"]["id"] == "entity1"
        assert result["entity"]["label"] == "Entity 1"
        
        # Verify mocks were called correctly
        self.mock_query_engine.query_entity.assert_called_with("entity1")
        self.mock_query_engine.find_connections.assert_called_with("entity1", 1)
    
    def test_compare_entities_tool(self):
        """Test the compare_entities_tool function."""
        # Call the tool directly
        result = compare_entities_tool({
            "entity1_id": "entity1",
            "entity2_id": "entity2"
        }, self.transport_id)
        
        # Verify result
        assert "entities" in result
        assert "paths" in result
        assert result["entities"]["entity1"]["id"] == "entity1"
        assert result["entities"]["entity2"]["id"] == "entity2"
        
        # Verify mocks were called correctly
        self.mock_query_engine.query_entity.assert_any_call("entity1")
        self.mock_query_engine.query_entity.assert_any_call("entity2")
        self.mock_query_engine.find_paths.assert_called_with("entity1", "entity2", 3)
    
    def test_find_central_entities_tool(self):
        """Test the find_central_entities_tool function."""
        # Call the tool directly
        result = find_central_entities_tool({
            "limit": 5
        }, self.transport_id)
        
        # Verify result
        assert "entities" in result
        assert "total" in result
        assert result["entities"] == self.mock_query_engine.get_central_entities.return_value
        
        # Verify mock was called correctly
        self.mock_query_engine.get_central_entities.assert_called_with(5, None)
    
    def test_summarize_ontology_tool(self):
        """Test the summarize_ontology_tool function."""
        # Call the tool directly
        result = summarize_ontology_tool({}, self.transport_id)
        
        # Verify result
        assert "summary" in result
        assert "total_entities" in result["summary"]
        assert "total_relationships" in result["summary"]
        assert "entity_types" in result["summary"]
        assert "relationship_types" in result["summary"]
        assert "central_entities" in result["summary"]
        
        # Verify mocks were called correctly
        self.mock_query_engine.get_entity_types.assert_called_once()
        self.mock_query_engine.get_relationship_types.assert_called_once()
        self.mock_query_engine.get_central_entities.assert_called_once()