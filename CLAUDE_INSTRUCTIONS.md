[Server STDERR]: 2025-03-30 18:33:32,773 - app.mcp.handlers.core - INFO - Client connected: Crystal REPL Client 1.0.0 via 5ee3bbe3-abc5-474b-b2cc-45ba4f6fe8f7
[Server STDERR]: 2025-03-30 18:33:32,773 - app.mcp.handlers.core - INFO - Protocol version negotiation: client=0.0.0, server=0.5.0
2025-03-31T01:33:32.774567Z   INFO - mcp_client: MCP client initialized successfully with server.
[Server STDERR]: 2025-03-30 18:33:32,775 - app.mcp.server - ERROR - Error handling method cyberon/search
[Server STDERR]: Traceback (most recent call last):
[Server STDERR]:   File "/home/cam/repos/cyberon/app/mcp/server.py", line 233, in handle_message
[Server STDERR]:     result = handler(params, transport_id)
[Server STDERR]:   File "/home/cam/repos/cyberon/app/mcp/handlers/query.py", line 68, in entity_search_handler
[Server STDERR]:     query = params.get("query", "")
[Server STDERR]:             ^^^^^^^^^^
[Server STDERR]: AttributeError: 'str' object has no attribute 'get'