"""
Tests for the MCP server implementation.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from app.mcp.server import MCPServer
from app.mcp.transports.base import Transport

# Create a subclass of MCPServer for testing that doesn't register resource handlers
class TestMCPServerClass(MCPServer):
    def _register_core_handlers(self) -> None:
        """Register core request handlers for the MCP protocol."""
        # Core protocol handlers
        self.register_handler("initialize", MagicMock(return_value={"result": "success"}))
        self.register_handler("server/capabilities", MagicMock(return_value={"result": "success"}))
        
        # Work Package 2 - Query engine handlers
        self.register_handler("cyberon/search", MagicMock(return_value={"result": "success"}))
        self.register_handler("cyberon/entity", MagicMock(return_value={"result": "success"}))
        self.register_handler("cyberon/paths", MagicMock(return_value={"result": "success"}))
        self.register_handler("cyberon/connections", MagicMock(return_value={"result": "success"}))
        self.register_handler("cyberon/entity_types", MagicMock(return_value={"result": "success"}))
        self.register_handler("cyberon/relationship_types", MagicMock(return_value={"result": "success"}))
        
        # Mock resource handlers for testing
        self.register_handler("resources/list", MagicMock(return_value={"resources": []}))
        self.register_handler("resources/templates/list", MagicMock(return_value={"resourceTemplates": []}))
        self.register_handler("resources/read", MagicMock(return_value={"contents": []}))
        self.register_handler("resources/subscribe", MagicMock(return_value={}))
        self.register_handler("resources/unsubscribe", MagicMock(return_value={}))

class TestMCPServer:
    """Test suite for the MCP server."""
    
    def test_server_initialization(self):
        """Test that the server initializes correctly."""
        server = TestMCPServerClass()
        assert server is not None
        assert server.PROTOCOL_VERSION == "0.5.0"
        assert "protocol_version" in server.capabilities
        assert "server_info" in server.capabilities
        assert "supports" in server.capabilities
        
    def test_register_handler(self):
        """Test that handlers can be registered."""
        server = TestMCPServerClass()
        handler = MagicMock()
        
        # Register a custom handler
        server.register_handler("test/method", handler)
        
        # Verify the handler was registered
        assert "test/method" in server.request_handlers
        assert server.request_handlers["test/method"] == handler
    
    def test_register_transport(self):
        """Test that transports can be registered."""
        server = TestMCPServerClass()
        
        # Create a transport mock with required methods explicitly defined
        transport = MagicMock()
        transport.set_message_handler = MagicMock()
        
        # Register the transport
        transport_id = server.register_transport(transport)
        
        # Verify the transport was registered
        assert transport_id in server.transports
        assert server.transports[transport_id] == transport
        transport.set_message_handler.assert_called_once()
    
    def test_handle_valid_request(self):
        """Test handling a valid request."""
        server = TestMCPServerClass()
        
        # Mock transport ID
        transport_id = "test-transport"
        
        # Mock handler
        mock_handler = MagicMock(return_value={"result": "success"})
        server.register_handler("test/method", mock_handler)
        
        # Create a valid request
        request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "test/method",
            "params": {"test": "param"}
        }
        
        # Process the request
        response = server.handle_message(json.dumps(request), transport_id)
        
        # Verify the handler was called
        mock_handler.assert_called_once_with({"test": "param"}, transport_id)
        
        # Verify the response
        response_obj = json.loads(response)
        assert response_obj["jsonrpc"] == "2.0"
        assert response_obj["id"] == "test-id"
        assert response_obj["result"] == {"result": "success"}
    
    def test_handle_invalid_request(self):
        """Test handling an invalid request."""
        server = TestMCPServerClass()
        
        # Test cases for invalid requests
        invalid_requests = [
            # Missing jsonrpc version
            {"id": "1", "method": "test", "params": {}},
            # Wrong jsonrpc version
            {"jsonrpc": "1.0", "id": "1", "method": "test", "params": {}},
            # Missing method
            {"jsonrpc": "2.0", "id": "1", "params": {}},
            # Non-existent method
            {"jsonrpc": "2.0", "id": "1", "method": "nonexistent", "params": {}}
        ]
        
        for req in invalid_requests:
            response = server.handle_message(json.dumps(req), "test-transport")
            response_obj = json.loads(response)
            
            # Verify error response structure
            assert response_obj["jsonrpc"] == "2.0"
            assert response_obj["id"] == req.get("id")
            assert "error" in response_obj
            assert "code" in response_obj["error"]
            assert "message" in response_obj["error"]
    
    def test_handler_exception(self):
        """Test that exceptions in handlers are properly handled."""
        server = TestMCPServerClass()
        
        # Create a handler that raises an exception
        def failing_handler(params, transport_id):
            raise ValueError("Test error")
        
        server.register_handler("test/failing", failing_handler)
        
        # Create a request that will trigger the failing handler
        request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "test/failing",
            "params": {}
        }
        
        # Process the request
        response = server.handle_message(json.dumps(request), "test-transport")
        
        # Verify the error response
        response_obj = json.loads(response)
        assert "error" in response_obj
        assert response_obj["error"]["code"] == -32603  # Internal error
        assert "Test error" in response_obj["error"]["data"]
    
    def test_invalid_json(self):
        """Test handling invalid JSON input."""
        server = TestMCPServerClass()
        
        # Process invalid JSON
        response = server.handle_message("this is not json", "test-transport")
        
        # Verify the error response
        response_obj = json.loads(response)
        assert "error" in response_obj
        assert response_obj["error"]["code"] == -32700  # Parse error