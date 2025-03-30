# client.py
"""
Example MCP client implementation for the CYBERON project.

This module provides a reference implementation of an MCP client that connects to the CYBERON MCP server. It demonstrates:
1. Proper initialization and capability negotiation
2. Correct JSON-RPC message formatting and handling
3. Structured error handling and recovery
4. Examples for all supported MCP methods
"""

import json
import logging
import uuid
from typing import Dict, Any, List, Optional, Union, Tuple

logger = logging.getLogger(__name__)

class MCPClient:
    """
    Model Context Protocol client implementation.
    
    This client can connect to any MCP-compatible server, with specific
    support for the CYBERON ontology features.
    """
    
    def __init__(self, transport=None):
        """
        Initialize the MCP client.
        
        Args:
            transport: Optional transport to use (if None, must be set later)
        """
        self.transport = transport
        self.next_id = 1
        self.initialized = False
        self.server_capabilities = {}
        self.client_info = {
            "name": "CYBERON MCP Client",
            "version": "0.1.0"
        }
        
        logger.info("MCP client initialized")
    
    def set_transport(self, transport):
        """
        Set the transport for the client.
        
        Args:
            transport: The transport to use
        """
        self.transport = transport
    
    def initialize(self) -> Dict[str, Any]:
        """
        Initialize the connection with the MCP server.
        
        Returns:
            Server initialization response
        
        Raises:
            RuntimeError: If the client is not connected to a transport
            ValueError: If the server returned an error
        """
        if not self.transport:
            raise RuntimeError("No transport set for the client")
        
        response = self._send_request("initialize", {
            "client_info": self.client_info
        })
        
        if "error" in response:
            raise ValueError(f"Error initializing MCP connection: {response['error']}")
        
        result = response.get("result", {})
        self.server_capabilities = result.get("capabilities", {})
        self.initialized = True
        
        logger.info("MCP client initialized with server")
        logger.debug(f"Server capabilities: {self.server_capabilities}")
        
        return result
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the server capabilities.
        
        Returns:
            Server capabilities
        
        Raises:
            RuntimeError: If the client is not initialized
        """
        self._ensure_initialized()
        
        response = self._send_request("server/capabilities", {})
        
        if "error" in response:
            logger.error(f"Error getting server capabilities: {response['error']}")
            return {}
        
        return response.get("result", {})
    
    def search_entities(self, query: str, entity_types: Optional[List[str]] = None, limit: int = 10) -> Dict[str, Any]:
        """
        Search for entities in the cybernetics ontology.
        
        Args:
            query: The search query
            entity_types: Optional list of entity types to filter by
            limit: Maximum number of results to return
            
        Returns:
            Search results
        """
        self._ensure_initialized()
        
        params = {
            "query": query,
            "limit": limit
        }
        
        if entity_types:
            params["entity_types"] = entity_types
        
        response = self._send_request("cyberon/search", params)
        
        if "error" in response:
            logger.error(f"Error searching entities: {response['error']}")
            return {"entities": [], "error": response["error"], "query": query}
        
        return response.get("result", {"entities": []})
    
    def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """
        Get detailed information about an entity.
        
        Args:
            entity_id: The ID of the entity to retrieve
            
        Returns:
            Entity details
        """
        self._ensure_initialized()
        
        response = self._send_request("cyberon/entity", {
            "entity_id": entity_id
        })
        
        if "error" in response:
            logger.error(f"Error getting entity {entity_id}: {response['error']}")
            return {"error": response["error"]}
        
        return response.get("result", {})
    
    def find_paths(self, source_id: str, target_id: str, max_length: int = 3) -> Dict[str, Any]:
        """
        Find paths between entities in the ontology.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            max_length: Maximum path length
            
        Returns:
            Paths between entities
        """
        self._ensure_initialized()
        
        response = self._send_request("cyberon/paths", {
            "source_id": source_id,
            "target_id": target_id,
            "max_length": max_length
        })
        
        if "error" in response:
            logger.error(f"Error finding paths: {response['error']}")
            return {"error": response["error"]}
        
        return response.get("result", {"paths": []})
    
    def find_connections(self, entity_id: str, max_distance: int = 2) -> Dict[str, Any]:
        """
        Find connected entities in the ontology.
        
        Args:
            entity_id: Entity ID to find connections for
            max_distance: Maximum distance to search
            
        Returns:
            Connected entities
        """
        self._ensure_initialized()
        
        response = self._send_request("cyberon/connections", {
            "entity_id": entity_id,
            "max_distance": max_distance
        })
        
        if "error" in response:
            logger.error(f"Error finding connections: {response['error']}")
            return {"error": response["error"]}
        
        return response.get("result", {"connections": {}})
    
    def get_entity_types(self) -> Dict[str, Any]:
        """
        Get all entity types in the ontology.
        
        Returns:
            Entity types and their counts
        """
        self._ensure_initialized()
        
        response = self._send_request("cyberon/entity_types", {})
        
        if "error" in response:
            logger.error(f"Error getting entity types: {response['error']}")
            return {"error": response["error"]}
        
        return response.get("result", {})
    
    def get_relationship_types(self) -> Dict[str, Any]:
        """
        Get all relationship types in the ontology.
        
        Returns:
            Relationship types and their counts
        """
        self._ensure_initialized()
        
        response = self._send_request("cyberon/relationship_types", {})
        
        if "error" in response:
            logger.error(f"Error getting relationship types: {response['error']}")
            return {"error": response["error"]}
        
        return response.get("result", {})
    
    def list_resources(self, cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        List available resources.
        
        Args:
            cursor: Optional pagination cursor
            
        Returns:
            List of resources
        """
        self._ensure_initialized()
        self._ensure_feature("resources")
        
        params = {}
        if cursor:
            params["cursor"] = cursor
        
        response = self._send_request("resources/list", params)
        
        if "error" in response:
            logger.error(f"Error listing resources: {response['error']}")
            return {"resources": [], "error": response["error"]}
        
        return response.get("result", {"resources": []})
    
    def list_resource_templates(self, cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        List available resource templates.
        
        Args:
            cursor: Optional pagination cursor
            
        Returns:
            List of resource templates
        """
        self._ensure_initialized()
        self._ensure_feature("resources")
        
        params = {}
        if cursor:
            params["cursor"] = cursor
        
        response = self._send_request("resources/templates/list", params)
        
        if "error" in response:
            logger.error(f"Error listing resource templates: {response['error']}")
            return {"templates": [], "error": response["error"]}
        
        return response.get("result", {"templates": []})
    
    def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Read a resource.
        
        Args:
            uri: The URI of the resource to read
            
        Returns:
            Resource contents
        """
        self._ensure_initialized()
        self._ensure_feature("resources")
        
        response = self._send_request("resources/read", {
            "uri": uri
        })
        
        if "error" in response:
            logger.error(f"Error reading resource {uri}: {response['error']}")
            return {"error": response["error"]}
        
        return response.get("result", {"contents": []})
    
    def subscribe_resource(self, uri: str) -> Dict[str, Any]:
        """
        Subscribe to resource updates.
        
        Args:
            uri: The URI of the resource to subscribe to
            
        Returns:
            Subscription result
        """
        self._ensure_initialized()
        self._ensure_feature("resources")
        
        response = self._send_request("resources/subscribe", {
            "uri": uri
        })
        
        if "error" in response:
            logger.error(f"Error subscribing to resource {uri}: {response['error']}")
            return {"error": response["error"]}
        
        return response.get("result", {})
    
    def unsubscribe_resource(self, uri: str) -> Dict[str, Any]:
        """
        Unsubscribe from resource updates.
        
        Args:
            uri: The URI of the resource to unsubscribe from
            
        Returns:
            Unsubscription result
        """
        self._ensure_initialized()
        self._ensure_feature("resources")
        
        response = self._send_request("resources/unsubscribe", {
            "uri": uri
        })
        
        if "error" in response:
            logger.error(f"Error unsubscribing from resource {uri}: {response['error']}")
            return {"error": response["error"]}
        
        return response.get("result", {})
    
    def list_tools(self) -> Dict[str, Any]:
        """
        List available tools.
        
        Returns:
            List of tools
        """
        self._ensure_initialized()
        self._ensure_feature("tools")
        
        response = self._send_request("tools/list", {})
        
        if "error" in response:
            logger.error(f"Error listing tools: {response['error']}")
            return {"tools": [], "error": response["error"]}
        
        return response.get("result", {"tools": []})
    
    def get_tool_schema(self, name: str) -> Dict[str, Any]:
        """
        Get the schema for a tool.
        
        Args:
            name: The name of the tool
            
        Returns:
            Tool schema
        """
        self._ensure_initialized()
        self._ensure_feature("tools")
        
        response = self._send_request("tools/schema", {
            "name": name
        })
        
        if "error" in response:
            logger.error(f"Error getting tool schema for {name}: {response['error']}")
            return {"error": response["error"]}
        
        return response.get("result", {})
    
    def execute_tool(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool.
        
        Args:
            name: The name of the tool to execute
            params: Parameters for the tool
            
        Returns:
            Tool execution result
        """
        self._ensure_initialized()
        self._ensure_feature("tools")
        
        response = self._send_request("tools/execute", {
            "name": name,
            "params": params
        })
        
        if "error" in response:
            logger.error(f"Error executing tool {name}: {response['error']}")
            return {"error": response["error"]}
        
        return response.get("result", {})
    
    def list_prompts(self) -> Dict[str, Any]:
        """
        List available prompts.
        
        Returns:
            List of prompts
        """
        self._ensure_initialized()
        self._ensure_feature("prompts")
        
        response = self._send_request("prompts/list", {})
        
        if "error" in response:
            logger.error(f"Error listing prompts: {response['error']}")
            return {"prompts": [], "error": response["error"]}
        
        return response.get("result", {"prompts": []})
    
    def get_prompt(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a prompt with parameters filled in.
        
        Args:
            name: The name of the prompt
            params: Parameters for the prompt
            
        Returns:
            The processed prompt
        """
        self._ensure_initialized()
        self._ensure_feature("prompts")
        
        response = self._send_request("prompts/get", {
            "name": name,
            "params": params
        })
        
        if "error" in response:
            logger.error(f"Error getting prompt {name}: {response['error']}")
            return {"error": response["error"]}
        
        return response.get("result", {})
    
    def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a request to the MCP server.
        
        Args:
            method: The method to call
            params: The parameters for the method
            
        Returns:
            The server response
            
        Raises:
            RuntimeError: If the client is not connected to a transport
        """
        if not self.transport:
            raise RuntimeError("No transport set for the client")
        
        request_id = self.next_id
        self.next_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        request_json = json.dumps(request)
        logger.debug(f"Sending request: {request_json}")
        
        response_json = self.transport.send_and_receive(request_json)
        logger.debug(f"Received response: {response_json}")
        
        try:
            return json.loads(response_json)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response_json}")
            return {"error": {"code": -32700, "message": "Invalid JSON response"}}
    
    def _ensure_initialized(self):
        """
        Ensure that the client is initialized.
        
        Raises:
            RuntimeError: If the client is not initialized
        """
        if not self.initialized:
            raise RuntimeError("MCP client not initialized")
    
    def _ensure_feature(self, feature: str):
        """
        Ensure that the server supports a specific feature.
        
        Args:
            feature: The feature to check for
            
        Raises:
            RuntimeError: If the feature is not supported
        """
        if not self.server_capabilities.get("supports", {}).get(feature, False):
            raise RuntimeError(f"Server does not support {feature}")

class StdioTransport:
    """
    Simple transport that communicates over standard input/output.
    
    This is useful for testing and for integration with command-line tools.
    """
    
    def __init__(self, mock_response=None):
        """
        Initialize the STDIO transport.
        
        Args:
            mock_response: Optional mock response for testing
        """
        self.mock_response = mock_response
    
    def send_and_receive(self, message: str) -> str:
        """
        Send a message and receive a response.
        
        Args:
            message: The message to send
            
        Returns:
            The response
        """
        # If we have a mock response (for testing), return it
        if self.mock_response is not None:
            return self.mock_response
            
        try:
            # Print the message to stdout
            print(message)
            
            # Read the response from stdin
            response = input()
            
            return response
        except Exception as e:
            # Return error response in case of exception
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": "Transport error",
                    "data": str(e)
                }
            }
            return json.dumps(error_response)


def demo_usage(use_mock=True):
    """
    Demonstrate usage of the MCP client.
    
    Args:
        use_mock: Whether to use mock responses for testing
    """
    if use_mock:
        # Create mock responses for testing
        mock_responses = [
            # Initialize response
            '{"jsonrpc":"2.0","id":1,"result":{"server_info":{"name":"CYBERON MCP Server","version":"0.1.0","vendor":"CYBERON Project"},"protocol_version":"0.5.0","supports":{"resources":true,"tools":true,"prompts":true}}}',
            # Capabilities response
            '{"jsonrpc":"2.0","id":2,"result":{"protocol_version":"0.5.0","server_info":{"name":"CYBERON MCP Server","version":"0.1.0","vendor":"CYBERON Project"},"supports":{"resources":true,"tools":true,"prompts":true}}}',
            # Search response
            '{"jsonrpc":"2.0","id":3,"result":{"entities":[{"id":"cybernetics","label":"Cybernetics","type":"concept","match_score":1.0},{"id":"first_order_cybernetics","label":"First-Order Cybernetics","type":"concept","match_score":0.8}],"query":"cybernetics","total":2}}',
            # Entity response
            '{"jsonrpc":"2.0","id":4,"result":{"id":"cybernetics","attributes":{"label":"Cybernetics","type":"concept"},"incoming":[],"outgoing":[]}}',
            # Connections response
            '{"jsonrpc":"2.0","id":5,"result":{"connections":{"1":[{"id":"first_order_cybernetics","label":"First-Order Cybernetics","type":"concept"}]},"entity":{"id":"cybernetics","label":"Cybernetics","type":"concept"}}}',
            # Tools list response
            '{"jsonrpc":"2.0","id":6,"result":{"tools":[{"name":"cyberon.tools.search","description":"Search for entities in the cybernetics ontology","schema":{"type":"object","properties":{"query":{"type":"string","description":"The search query"},"entity_types":{"type":"array","items":{"type":"string"},"description":"Optional filter by entity types"},"limit":{"type":"integer","description":"Maximum number of results to return","default":10}},"required":["query"]}}]}}',
            # Tool execution response
            '{"jsonrpc":"2.0","id":7,"result":{"name":"cyberon.tools.search","timestamp":"2023-07-14T15:21:36.123456","result":{"entities":[{"id":"feedback","label":"Feedback","type":"concept","match_score":1.0}],"query":"feedback","total":1}}}',
            # Prompts list response
            '{"jsonrpc":"2.0","id":8,"result":{"prompts":[{"name":"cyberon.prompts.entity_analysis","description":"Analyze a specific entity in the cybernetics ontology","parameter_schema":{"type":"object","properties":{"entity_id":{"type":"string","description":"The ID of the entity to analyze"}},"required":["entity_id"]},"usage_examples":[{"description":"Analyze the cybernetics concept","params":{"entity_id":"cybernetics"}}]}]}}',
            # Prompt get response
            '{"jsonrpc":"2.0","id":9,"result":{"name":"cyberon.prompts.entity_analysis","timestamp":"2023-07-14T15:21:36.123456","prompt":"Please analyze the topic of feedback loops within the cybernetics ontology.","context":{"topic":"feedback loops","search_results":[{"id":"feedback","label":"Feedback","type":"concept","match_score":1.0}]}}}'
        ]
        
        transport = StdioTransport(mock_responses[0])  # Start with first response
        transport.mock_responses = mock_responses      # Store all responses
        transport.response_index = 0                   # Track current response
        
        def get_next_response(*args, **kwargs):
            """Helper to cycle through mock responses."""
            transport.response_index = (transport.response_index + 1) % len(transport.mock_responses)
            return transport.mock_responses[transport.response_index]
        
        # Override send_and_receive to cycle through responses
        transport.send_and_receive = get_next_response
    else:
        # Use actual STDIO transport
        transport = StdioTransport()
    
    client = MCPClient(transport)
    
    # Initialize the connection
    try:
        client.initialize()
        print("Successfully initialized MCP connection")
    except Exception as e:
        print(f"Error initializing MCP connection: {e}")
        return
    
    # Get server capabilities
    capabilities = client.get_capabilities()
    print(f"Server capabilities: {capabilities}")
    
    # Search for entities
    search_results = client.search_entities("cybernetics", limit=5)
    print(f"Found {len(search_results.get('entities', []))} entities matching 'cybernetics'")
    
    # Get entity details
    if search_results.get('entities'):
        entity_id = search_results['entities'][0]['id']
        entity = client.get_entity(entity_id)
        print(f"Entity details: {entity}")
        
        # Find connections for this entity
        connections = client.find_connections(entity_id)
        print(f"Found {sum(len(conns) for conns in connections.get('connections', {}).values())} connections")
    
    # List tools if available
    if capabilities.get('supports', {}).get('tools'):
        tools = client.list_tools()
        print(f"Available tools: {[tool['name'] for tool in tools.get('tools', [])]}")
        
        # Execute a tool if available
        if tools.get('tools'):
            tool_name = tools['tools'][0]['name']
            tool_result = client.execute_tool(tool_name, {"query": "feedback"})
            print(f"Tool execution result: {tool_result}")
    
    # List prompts if available
    if capabilities.get('supports', {}).get('prompts'):
        prompts = client.list_prompts()
        print(f"Available prompts: {[prompt['name'] for prompt in prompts.get('prompts', [])]}")
        
        # Get a prompt if available
        if prompts.get('prompts'):
            prompt_name = prompts['prompts'][0]['name']
            prompt_result = client.get_prompt(prompt_name, {"topic": "feedback loops"})
            print(f"Prompt result: {prompt_result}")
    
    print("MCP client demo completed")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run demo with mock responses to avoid stdin/stdout issues
    demo_usage(use_mock=False)


    