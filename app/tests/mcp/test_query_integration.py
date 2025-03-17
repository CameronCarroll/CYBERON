"""
Tests for the integration between the MCP server and the CyberneticsQueryEngine.

These tests verify that the MCP server correctly passes queries to the query engine
and returns appropriate responses.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch

from app.mcp import MCPServer
from app.mcp.handlers.query import (
    set_query_engine,
    entity_search_handler,
    entity_info_handler,
    find_paths_handler,
    find_connections_handler
)

# Sample test data
TEST_ENTITY_ID = "test_entity_1"
TEST_SOURCE_ID = "test_entity_1"
TEST_TARGET_ID = "test_entity_2"
TEST_QUERY = "test"
TEST_TRANSPORT_ID = "test_transport_001"

@pytest.fixture
def mock_query_engine():
    """Create a mock CyberneticsQueryEngine for testing."""
    mock_engine = Mock()
    
    # Setup mock responses
    mock_engine.search_entities.return_value = [
        {"id": "test_entity_1", "label": "Test Entity 1", "type": "test", "match_score": 1.0},
        {"id": "test_entity_2", "label": "Test Entity 2", "type": "test", "match_score": 0.8}
    ]
    
    mock_engine.query_entity.return_value = {
        "id": TEST_ENTITY_ID,
        "attributes": {"label": "Test Entity", "type": "test"},
        "incoming": [],
        "outgoing": []
    }
    
    mock_engine.find_paths.return_value = [
        [
            {"id": TEST_SOURCE_ID, "label": "Source", "type": "test", "relationship_to_next": "related_to"},
            {"id": TEST_TARGET_ID, "label": "Target", "type": "test"}
        ]
    ]
    
    mock_engine.find_connections.return_value = {
        1: [{"id": "test_entity_2", "label": "Test Entity 2", "type": "test"}],
        2: []
    }
    
    mock_engine.get_entity_types.return_value = {"test": 5, "concept": 3}
    mock_engine.get_relationship_types.return_value = {"related_to": 4, "part_of": 2}
    
    return mock_engine

@pytest.fixture
def mcp_server_with_query_engine(mock_query_engine):
    """Create an MCP server with the mock query engine."""
    server = MCPServer()
    server.set_query_engine(mock_query_engine)
    return server

def test_entity_search_handler(mock_query_engine):
    """Test that the entity search handler correctly queries the engine."""
    # Set the global query engine
    set_query_engine(mock_query_engine)
    
    # Test with a basic query
    params = {"query": TEST_QUERY}
    result = entity_search_handler(params, TEST_TRANSPORT_ID)
    
    # Check that the query engine was called correctly
    mock_query_engine.search_entities.assert_called_once_with(TEST_QUERY, None)
    
    # Check the response format
    assert "entities" in result
    assert len(result["entities"]) == 2
    assert result["query"] == TEST_QUERY
    assert result["total"] == 2
    assert result["entities"][0]["id"] == "test_entity_1"
    
    # Test with entity_types filter
    params = {"query": TEST_QUERY, "entity_types": ["test"]}
    entity_search_handler(params, TEST_TRANSPORT_ID)
    
    # Check that entity_types was passed correctly
    mock_query_engine.search_entities.assert_called_with(TEST_QUERY, ["test"])

def test_entity_info_handler(mock_query_engine):
    """Test that the entity info handler correctly queries the engine."""
    # Set the global query engine
    set_query_engine(mock_query_engine)
    
    # Test with a valid entity ID
    params = {"entity_id": TEST_ENTITY_ID}
    result = entity_info_handler(params, TEST_TRANSPORT_ID)
    
    # Check that the query engine was called correctly
    mock_query_engine.query_entity.assert_called_once_with(TEST_ENTITY_ID)
    
    # Check the response format
    assert result["id"] == TEST_ENTITY_ID
    assert "attributes" in result
    assert "incoming" in result
    assert "outgoing" in result
    
    # Test with missing entity ID
    params = {}
    result = entity_info_handler(params, TEST_TRANSPORT_ID)
    assert "error" in result

def test_find_paths_handler(mock_query_engine):
    """Test that the find paths handler correctly queries the engine."""
    # Set the global query engine
    set_query_engine(mock_query_engine)
    
    # Test with valid source and target IDs
    params = {"source_id": TEST_SOURCE_ID, "target_id": TEST_TARGET_ID}
    result = find_paths_handler(params, TEST_TRANSPORT_ID)
    
    # Check that the query engine was called correctly
    mock_query_engine.find_paths.assert_called_once_with(TEST_SOURCE_ID, TEST_TARGET_ID, 3)
    mock_query_engine.query_entity.assert_any_call(TEST_SOURCE_ID)
    mock_query_engine.query_entity.assert_any_call(TEST_TARGET_ID)
    
    # Check the response format
    assert "paths" in result
    assert "source" in result
    assert "target" in result
    assert "count" in result
    assert len(result["paths"]) == 1
    
    # Test with missing source ID
    params = {"target_id": TEST_TARGET_ID}
    result = find_paths_handler(params, TEST_TRANSPORT_ID)
    assert "error" in result

def test_find_connections_handler(mock_query_engine):
    """Test that the find connections handler correctly queries the engine."""
    # Set the global query engine
    set_query_engine(mock_query_engine)
    
    # Test with a valid entity ID
    params = {"entity_id": TEST_ENTITY_ID}
    result = find_connections_handler(params, TEST_TRANSPORT_ID)
    
    # Check that the query engine was called correctly
    mock_query_engine.find_connections.assert_called_once_with(TEST_ENTITY_ID, 2)
    mock_query_engine.query_entity.assert_called_with(TEST_ENTITY_ID)
    
    # Check the response format
    assert "connections" in result
    assert "entity" in result
    assert 1 in result["connections"]
    assert len(result["connections"][1]) == 1
    
    # Test with missing entity ID
    params = {}
    result = find_connections_handler(params, TEST_TRANSPORT_ID)
    assert "error" in result

def test_mcp_server_json_rpc_format(mcp_server_with_query_engine):
    """Test the MCP server JSON-RPC message format for query engine integration."""
    server = mcp_server_with_query_engine
    
    # Test entity search message
    search_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "cyberon/search",
        "params": {"query": TEST_QUERY}
    })
    
    search_response = server.handle_message(search_message, TEST_TRANSPORT_ID)
    search_result = json.loads(search_response)
    
    assert search_result["jsonrpc"] == "2.0"
    assert search_result["id"] == 1
    assert "result" in search_result
    assert "entities" in search_result["result"]
    
    # Test entity info message
    info_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "cyberon/entity",
        "params": {"entity_id": TEST_ENTITY_ID}
    })
    
    info_response = server.handle_message(info_message, TEST_TRANSPORT_ID)
    info_result = json.loads(info_response)
    
    assert info_result["jsonrpc"] == "2.0"
    assert info_result["id"] == 2
    assert "result" in info_result
    assert info_result["result"]["id"] == TEST_ENTITY_ID

def test_session_management():
    """Test that session management works correctly."""
    from app.mcp.handlers.query import _get_or_create_session, SESSIONS
    
    # Clear any existing sessions
    SESSIONS.clear()
    
    # Get a new session
    session = _get_or_create_session(TEST_TRANSPORT_ID)
    
    # Check that the session was created with the expected structure
    assert TEST_TRANSPORT_ID in SESSIONS
    assert "recent_searches" in session
    assert "recent_entities" in session
    assert "recent_paths" in session
    
    # Modify the session
    session["recent_searches"].append(TEST_QUERY)
    
    # Get the same session again and check that modifications persist
    same_session = _get_or_create_session(TEST_TRANSPORT_ID)
    assert same_session["recent_searches"] == [TEST_QUERY]
    
    # Get a different session
    other_session = _get_or_create_session("other_transport")
    assert other_session["recent_searches"] == []

def test_error_handling(mock_query_engine):
    """Test that error handling works correctly."""
    # Set the global query engine
    set_query_engine(mock_query_engine)
    
    # Make the query engine raise an exception
    mock_query_engine.search_entities.side_effect = Exception("Test error")
    
    # Test with a basic query
    params = {"query": TEST_QUERY}
    result = entity_search_handler(params, TEST_TRANSPORT_ID)
    
    # Check that the error was handled
    assert "error" in result
    assert "Test error" in result["error"]