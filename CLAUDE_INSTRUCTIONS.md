/home/cam/repos/cyberon [git::main *] [cam@brill] [17:52]
> crystal src/test_client.cr 
======================================================================
CRYSTAL MCP TEST CLIENT
======================================================================
Server path: /home/cam/repos/cyberon/mcp_server.py
Creating transport and launching server...
2025-03-31T00:52:10.831469Z   INFO - mcp_transport.process: ProcessTransport initialized with server path: /home/cam/repos/cyberon/mcp_server.py
2025-03-31T00:52:10.831475Z   INFO - mcp_transport.process: Launching MCP server process from: /home/cam/repos/cyberon/mcp_server.py
Server process launched successfully!
Creating MCP client...
Initializing connection...
2025-03-31T00:52:10.832181Z   INFO - mcp_transport.process: Server process launched with PID: 554943
2025-03-31T00:52:10.832218Z   INFO - mcp_client: MCP client created. Transport set.
[Server STDERR]: 2025-03-30 17:52:11,150 - __main__ - INFO - Starting CYBERON MCP Server...
[Server STDERR]: 2025-03-30 17:52:11,150 - app.mcp.server - INFO - MCP Server initialized with protocol version 0.5.0
[Server STDERR]: 2025-03-30 17:52:11,150 - __main__ - ERROR - Data file not found: data/cybernetics_ontology.json
[Server STDERR]: 2025-03-30 17:52:11,150 - __main__ - WARNING - Running without query engine - some functionality will be limited
[Server STDERR]: 2025-03-30 17:52:11,150 - __main__ - WARNING - Running without query engine - some functionality will be limited
[Server STDERR]: 2025-03-30 17:52:11,150 - app.mcp.server - INFO - Registered transport 14ad8dc6-6ba3-450f-847c-51c573968fd0 of type StdioTransport
[Server STDERR]: 2025-03-30 17:52:11,150 - __main__ - INFO - StdioTransport registered with ID: 14ad8dc6-6ba3-450f-847c-51c573968fd0
[Server STDERR]: 2025-03-30 17:52:11,150 - __main__ - INFO - Entering StdioTransport async context...
[Server STDERR]: 2025-03-30 17:52:11,153 - app.mcp.transports.stdio - INFO - StdioTransport activated and reader task started.
[Server STDERR]: 2025-03-30 17:52:11,153 - app.mcp.transports.stdio - INFO - StdioTransport [14ad8dc6-6ba3-450f-847c-51c573968fd0] started and ready.
[Server STDERR]: 2025-03-30 17:52:11,153 - __main__ - INFO - StdioTransport [14ad8dc6-6ba3-450f-847c-51c573968fd0] is active. Server ready.
[Server STDERR]: 2025-03-30 17:52:11,154 - app.mcp.transports.stdio - INFO - StdioTransport [14ad8dc6-6ba3-450f-847c-51c573968fd0] reader loop activated and starting.
[Server STDERR]: 2025-03-30 17:52:11,154 - app.mcp.handlers.core - INFO - Client connected: Unknown Client Unknown Version via 14ad8dc6-6ba3-450f-847c-51c573968fd0
[Server STDERR]: 2025-03-30 17:52:11,154 - app.mcp.handlers.core - INFO - Protocol version negotiation: client=0.0.0, server=0.5.0
UNEXPECTED ERROR: KeyError - Missing hash key: "capabilities"
  /usr/lib/crystal/hash.cr:1193:11 in '[]'
  src/mcp_client.cr:95:30 in 'init_connection'
  src/test_client.cr:97:17 in '__crystal_main'
  /usr/lib/crystal/crystal/main.cr:118:5 in 'main_user_code'
  /usr/lib/crystal/crystal/main.cr:104:7 in 'main'
  /usr/lib/crystal/crystal/system/unix/main.cr:9:3 in 'main'
  /usr/lib/libc.so.6 in '??'
  /usr/lib/libc.so.6 in '__libc_start_main'
  /home/cam/.cache/crystal/crystal-run-test_client.tmp in '_start'
  ???