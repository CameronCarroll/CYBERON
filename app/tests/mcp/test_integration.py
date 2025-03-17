"""
Integration tests for the MCP server components.

These tests verify that all MCP components (core, query, resources, tools, prompts)
work together correctly in an end-to-end fashion.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch

from app.mcp import MCPServer
from app.models.query_engine import CyberneticsQueryEngine

# Test constants
TEST_ENTITY_ID = "test_entity_1"
TEST_SOURCE_ID = "test_entity_1"
TEST_TARGET_ID = "test_entity_2"
TEST_QUERY = "test"
TEST_TRANSPORT_ID = "test_transport_001"
TEST_CONCEPT_ID = "test_concept_1"

class TestTransport:
    """Mock transport for testing the MCP server."""
    
    def __init__(self):
        self.message_handler = None
        self.messages_sent = []
    
    def set_message_handler(self, handler):
        """Set the message handler."""
        self.message_handler = handler
    
    def send_message(self, message):
        """Record sent messages for inspection."""
        self.messages_sent.append(message)
    
    def start(self):
        """Mock start method."""
        pass
    
    def stop(self):
        """Mock stop method."""
        pass
    
    def simulate_message(self, message):
        """Simulate receiving a message."""
        if self.message_handler:
            return self.message_handler(message, TEST_TRANSPORT_ID)
        return None

@pytest.fixture
def mock_query_engine():
    """Create a mock query engine with test data."""
    mock_engine = Mock(spec=CyberneticsQueryEngine)
    
    # Mock search entities
    mock_engine.search_entities.return_value = [
        {"id": "test_entity_1", "label": "Test Entity 1", "type": "test", "match_score": 1.0},
        {"id": "test_entity_2", "label": "Test Entity 2", "type": "test", "match_score": 0.8}
    ]
    
    # Mock query entity
    mock_entity = {
        "id": TEST_ENTITY_ID,
        "attributes": {"label": "Test Entity", "type": "test"},
        "incoming": [],
        "outgoing": []
    }
    mock_engine.query_entity.return_value = mock_entity
    
    # Side effect function to return different entities for different IDs
    def query_entity_side_effect(entity_id):
        if entity_id == TEST_ENTITY_ID:
            return mock_entity
        elif entity_id == TEST_TARGET_ID:
            return {
                "id": TEST_TARGET_ID,
                "attributes": {"label": "Test Entity 2", "type": "test"},
                "incoming": [],
                "outgoing": []
            }
        elif entity_id == TEST_CONCEPT_ID:
            return {
                "id": TEST_CONCEPT_ID,
                "attributes": {"label": "Test Concept", "type": "concept"},
                "incoming": [],
                "outgoing": []
            }
        else:
            return {"error": f"Entity not found: {entity_id}"}
    
    mock_engine.query_entity.side_effect = query_entity_side_effect
    
    # Mock find paths
    mock_engine.find_paths.return_value = [
        [
            {"id": TEST_SOURCE_ID, "label": "Source", "type": "test", "relationship_to_next": "related_to"},
            {"id": TEST_TARGET_ID, "label": "Target", "type": "test"}
        ]
    ]
    
    # Mock find connections - use integers as keys
    mock_engine.find_connections.return_value = {
        1: [{"id": "test_entity_2", "label": "Test Entity 2", "type": "test"}],
        2: []
    }
    
    # Mock entity and relationship types
    mock_engine.get_entity_types.return_value = {"test": 5, "concept": 3}
    mock_engine.get_relationship_types.return_value = {"related_to": 4, "part_of": 2}
    
    # Mock central entities
    mock_engine.get_central_entities.return_value = [
        {"id": "test_entity_1", "label": "Test Entity 1", "type": "test", "centrality": 0.9, "connections": 5},
        {"id": "test_entity_2", "label": "Test Entity 2", "type": "test", "centrality": 0.8, "connections": 4}
    ]
    
    # Mock concept hierarchy
    mock_engine.analyze_concept_hierarchy.return_value = {
        "root_nodes": [
            {"id": "test_concept_1", "label": "Test Concept", "type": "concept", "max_depth": 2}
        ],
        "hierarchies": {
            "test_concept_1": {
                "0": [{"id": "test_concept_1", "label": "Test Concept", "type": "concept"}],
                "1": [{"id": "test_sub_concept", "label": "Test Sub-Concept", "type": "concept"}]
            }
        }
    }
    
    # Mock related concepts
    mock_engine.get_related_concepts.return_value = {
        "related_to": [
            {"id": "test_entity_2", "label": "Test Entity 2", "type": "test", "direction": "outgoing"}
        ],
        "part_of": []
    }
    
    # Mock concept evolution
    mock_engine.get_concept_evolution.return_value = [
        [
            {"id": "test_concept_1", "label": "Test Concept", "type": "concept"},
            {"id": "test_sub_concept", "label": "Test Sub-Concept", "type": "concept"}
        ]
    ]
    
    # Mock ontology summary
    mock_engine.generate_ontology_summary.return_value = {
        "node_count": 8,
        "edge_count": 12,
        "entity_types": {"test": 5, "concept": 3}
    }
    
    # Mock section by topic
    mock_engine.find_section_by_topic.return_value = [
        {"id": "section_1", "title": "Test Section", "content": "This is test content."}
    ]
    
    # Add structured_ontology for resources testing
    mock_engine.structured_ontology = {
        1: {"title": "Section 1", "content": "This is section 1 content."},
        2: {"title": "Section 2", "content": "This is section 2 content."}
    }
    
    # Add get_all_resources for resources list
    mock_engine.get_all_resources = Mock(return_value=[
        {"name": "Test Resource 1", "uri": "cyberon:///entity/test_entity_1", "description": "Test resource 1"},
        {"name": "Test Resource 2", "uri": "cyberon:///entity/test_entity_2", "description": "Test resource 2"}
    ])
    
    # Add get_resource_templates
    mock_engine.get_resource_templates = Mock(return_value=[
        {"name": "Entity Template", "uri_template": "cyberon:///entity/{id}", "description": "Get entity by ID"}
    ])
    
    # Add read_resource
    mock_engine.read_resource = Mock(return_value={
        "contents": [
            {"uri": f"cyberon:///entity/{TEST_ENTITY_ID}", "mimeType": "application/json", "text": json.dumps(mock_entity)}
        ]
    })
    
    return mock_engine

@pytest.fixture
def mcp_server(mock_query_engine):
    """Create an MCP server with mock query engine and test transport."""
    server = MCPServer()
    
    # Register the mock query engine
    server.set_query_engine(mock_query_engine)
    
    # Create and register a test transport
    transport = TestTransport()
    server.register_transport(transport)
    
    # Return both the server and transport for testing
    return (server, transport)

def test_server_initialization(mcp_server):
    """Test that the server initializes correctly."""
    server, transport = mcp_server
    
    # Test initialization message
    init_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "client_info": {
                "name": "Test Client",
                "version": "1.0.0"
            }
        }
    })
    
    response = transport.simulate_message(init_message)
    response_data = json.loads(response)
    
    assert response_data["jsonrpc"] == "2.0"
    assert response_data["id"] == 1
    assert "result" in response_data
    assert "server_info" in response_data["result"]
    # The result might have either "capabilities" or keys like "protocol_version" and "supports"
    assert ("capabilities" in response_data["result"] or
            ("protocol_version" in response_data["result"] and "supports" in response_data["result"]))
    
    # Test capabilities message
    capabilities_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "server/capabilities",
        "params": {}
    })
    
    response = transport.simulate_message(capabilities_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "protocol_version" in response_data["result"]
    assert "supports" in response_data["result"]
    assert response_data["result"]["supports"]["resources"] is True
    assert response_data["result"]["supports"]["tools"] is True
    assert response_data["result"]["supports"]["prompts"] is True

def test_query_integration(mcp_server, mock_query_engine):
    """Test integration of query functionality."""
    server, transport = mcp_server
    
    # Test search
    search_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "cyberon/search",
        "params": {
            "query": TEST_QUERY
        }
    })
    
    response = transport.simulate_message(search_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "entities" in response_data["result"]
    assert len(response_data["result"]["entities"]) == 2
    
    # Test entity info
    entity_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "cyberon/entity",
        "params": {
            "entity_id": TEST_ENTITY_ID
        }
    })
    
    response = transport.simulate_message(entity_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert response_data["result"]["id"] == TEST_ENTITY_ID
    
    # Test paths
    paths_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 5,
        "method": "cyberon/paths",
        "params": {
            "source_id": TEST_SOURCE_ID,
            "target_id": TEST_TARGET_ID
        }
    })
    
    response = transport.simulate_message(paths_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "paths" in response_data["result"]
    assert len(response_data["result"]["paths"]) == 1
    
    # Test connections
    connections_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 6,
        "method": "cyberon/connections",
        "params": {
            "entity_id": TEST_ENTITY_ID
        }
    })
    
    response = transport.simulate_message(connections_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "connections" in response_data["result"]
    assert "1" in response_data["result"]["connections"]

def test_resources_integration(mcp_server):
    """Test integration of resource functionality."""
    server, transport = mcp_server
    
    # Test resources list
    resources_list_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 7,
        "method": "resources/list",
        "params": {}
    })
    
    response = transport.simulate_message(resources_list_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "resources" in response_data["result"]
    
    # Test resources templates list
    templates_list_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 8,
        "method": "resources/templates/list",
        "params": {}
    })
    
    response = transport.simulate_message(templates_list_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    
    # Test resource read
    resource_read_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 9,
        "method": "resources/read",
        "params": {
            "uri": f"cyberon:///entity/{TEST_ENTITY_ID}"
        }
    })
    
    response = transport.simulate_message(resource_read_message)
    response_data = json.loads(response)
    
    assert "result" in response_data

def test_tools_integration(mcp_server, mock_query_engine):
    """Test integration of tool functionality."""
    server, transport = mcp_server
    
    # Test tools list
    tools_list_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/list",
        "params": {}
    })
    
    response = transport.simulate_message(tools_list_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "tools" in response_data["result"]
    assert len(response_data["result"]["tools"]) > 0
    
    # Test tool schema
    tool_schema_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 11,
        "method": "tools/schema",
        "params": {
            "name": "cyberon.tools.search"
        }
    })
    
    response = transport.simulate_message(tool_schema_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "schema" in response_data["result"]
    
    # Test basic tool execution
    search_tool_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 12,
        "method": "tools/execute",
        "params": {
            "name": "cyberon.tools.search",
            "params": {
                "query": TEST_QUERY
            }
        }
    })
    
    response = transport.simulate_message(search_tool_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "name" in response_data["result"]
    assert "timestamp" in response_data["result"]
    assert "result" in response_data["result"]
    assert response_data["result"]["name"] == "cyberon.tools.search"
    
    # Test advanced tool execution - concept hierarchy
    hierarchy_tool_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 13,
        "method": "tools/execute",
        "params": {
            "name": "cyberon.tools.concept_hierarchy",
            "params": {
                "root_concept_id": TEST_CONCEPT_ID
            }
        }
    })
    
    response = transport.simulate_message(hierarchy_tool_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "result" in response_data["result"]
    assert "root_concept" in response_data["result"]["result"]
    
    # Test advanced tool execution - related concepts
    related_tool_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 14,
        "method": "tools/execute",
        "params": {
            "name": "cyberon.tools.related_concepts",
            "params": {
                "concept_id": TEST_CONCEPT_ID
            }
        }
    })
    
    response = transport.simulate_message(related_tool_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "result" in response_data["result"]
    assert "related_concepts" in response_data["result"]["result"]
    
    # Test advanced tool execution - concept evolution
    evolution_tool_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 15,
        "method": "tools/execute",
        "params": {
            "name": "cyberon.tools.concept_evolution",
            "params": {
                "concept_id": TEST_CONCEPT_ID
            }
        }
    })
    
    response = transport.simulate_message(evolution_tool_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "result" in response_data["result"]
    assert "evolution_chains" in response_data["result"]["result"]

def test_prompts_integration(mcp_server, mock_query_engine):
    """Test integration of prompt functionality."""
    server, transport = mcp_server
    
    # Test prompts list
    prompts_list_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 16,
        "method": "prompts/list",
        "params": {}
    })
    
    response = transport.simulate_message(prompts_list_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "prompts" in response_data["result"]
    assert len(response_data["result"]["prompts"]) > 0
    
    # Test entity analysis prompt
    entity_prompt_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 17,
        "method": "prompts/get",
        "params": {
            "name": "cyberon.prompts.entity_analysis",
            "params": {
                "entity_id": TEST_ENTITY_ID
            }
        }
    })
    
    response = transport.simulate_message(entity_prompt_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "name" in response_data["result"]
    assert "prompt" in response_data["result"]
    assert "context" in response_data["result"]
    assert "entity" in response_data["result"]["context"]
    
    # Test concept comparison prompt
    comparison_prompt_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 18,
        "method": "prompts/get",
        "params": {
            "name": "cyberon.prompts.concept_comparison",
            "params": {
                "concept1_id": TEST_ENTITY_ID,
                "concept2_id": TEST_TARGET_ID
            }
        }
    })
    
    response = transport.simulate_message(comparison_prompt_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "prompt" in response_data["result"]
    assert "context" in response_data["result"]
    assert "concept1" in response_data["result"]["context"]
    assert "concept2" in response_data["result"]["context"]
    
    # Test ontology exploration prompt
    exploration_prompt_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 19,
        "method": "prompts/get",
        "params": {
            "name": "cyberon.prompts.ontology_exploration",
            "params": {
                "topic": TEST_QUERY
            }
        }
    })
    
    response = transport.simulate_message(exploration_prompt_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "prompt" in response_data["result"]
    assert "context" in response_data["result"]

def test_error_handling(mcp_server):
    """Test error handling in integrated components."""
    server, transport = mcp_server
    
    # Test method not found
    invalid_method_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 20,
        "method": "invalid_method",
        "params": {}
    })
    
    response = transport.simulate_message(invalid_method_message)
    response_data = json.loads(response)
    
    assert "error" in response_data
    assert response_data["error"]["code"] == -32601  # Method not found
    
    # Test invalid params
    invalid_params_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 21,
        "method": "cyberon/entity",
        "params": {}  # Missing required entity_id
    })
    
    response = transport.simulate_message(invalid_params_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "error" in response_data["result"]
    
    # Test tool not found
    invalid_tool_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 22,
        "method": "tools/execute",
        "params": {
            "name": "invalid_tool",
            "params": {}
        }
    })
    
    response = transport.simulate_message(invalid_tool_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "error" in response_data["result"]
    
    # Test prompt not found
    invalid_prompt_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 23,
        "method": "prompts/get",
        "params": {
            "name": "invalid_prompt",
            "params": {}
        }
    })
    
    response = transport.simulate_message(invalid_prompt_message)
    response_data = json.loads(response)
    
    assert "result" in response_data
    assert "error" in response_data["result"]