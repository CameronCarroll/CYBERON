Launching MCP server process...
Server process launched (PID: 504197).
Started thread to monitor server stderr.
[Server STDERR]: 2025-03-30 17:08:21,982 - __main__ - INFO - Starting CYBERON MCP Server...
[Server STDERR]: 2025-03-30 17:08:21,982 - app.mcp.server - INFO - MCP Server initialized with protocol version 0.5.0
[Server STDERR]: 2025-03-30 17:08:21,982 - __main__ - WARNING - Running without query engine - some functionality will be limited
[Server STDERR]: 2025-03-30 17:08:21,982 - app.mcp.server - INFO - Registered transport b43eba67-fe52-4b6d-a322-04e5c95d0085 of type StdioTransport
[Server STDERR]: 2025-03-30 17:08:21,982 - __main__ - INFO - StdioTransport registered with ID: b43eba67-fe52-4b6d-a322-04e5c95d0085
[Server STDERR]: 2025-03-30 17:08:21,982 - __main__ - INFO - Entering StdioTransport async context...
[Server STDERR]: 2025-03-30 17:08:21,986 - app.mcp.transports.stdio - INFO - StdioTransport activated and reader task started.
[Server STDERR]: 2025-03-30 17:08:21,986 - app.mcp.transports.stdio - INFO - StdioTransport [b43eba67-fe52-4b6d-a322-04e5c95d0085] started and ready.
[Server STDERR]: 2025-03-30 17:08:21,986 - __main__ - INFO - StdioTransport [b43eba67-fe52-4b6d-a322-04e5c95d0085] is active. Server ready.
[Server STDERR]: 2025-03-30 17:08:21,986 - app.mcp.transports.stdio - INFO - StdioTransport [b43eba67-fe52-4b6d-a322-04e5c95d0085] reader loop activated and starting.
[Server STDERR]: 2025-03-30 17:08:21,986 - app.mcp.transports.stdio - ERROR - StdioTransport [b43eba67-fe52-4b6d-a322-04e5c95d0085] error receiving/processing message: '_io.BufferedReader' object has no attribute 'receive'
[Server STDERR]: Traceback (most recent call last):
[Server STDERR]: File "/home/cam/repos/cyberon/app/mcp/transports/stdio.py", line 71, in _reader_loop
[Server STDERR]: message = await receive_stream.receive()
[Server STDERR]: ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
[Server STDERR]: File "/usr/lib/python3.13/site-packages/anyio/streams/text.py", line 47, in receive
[Server STDERR]: chunk = await self.transport_stream.receive()
[Server STDERR]: ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
[Server STDERR]: File "/usr/lib/python3.13/site-packages/anyio/_core/_fileio.py", line 71, in __getattr__
[Server STDERR]: return getattr(self._fp, name)
[Server STDERR]: AttributeError: '_io.BufferedReader' object has no attribute 'receive'
[Server STDERR]: 2025-03-30 17:08:21,987 - app.mcp.transports.stdio - INFO - StdioTransport [b43eba67-fe52-4b6d-a322-04e5c95d0085] reader loop finished.
[Server STDERR]: 2025-03-30 17:08:21,987 - app.mcp.transports.stdio - INFO - StdioTransport [b43eba67-fe52-4b6d-a322-04e5c95d0085] closing...
[Server STDERR]: 2025-03-30 17:08:21,987 - __main__ - INFO - StdioTransport context finished.
>-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->
SENDING JSON >>>
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"client_info": {"name": "Subprocess Test Client", "version": "1.0.0"}}}
>-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->-->
Flushed server stdin.
Closed server stdin.
<--<--<--<--<--<--<--<--<--<--<--<--<--<--<--<--<--<--<--<--<--<--<--<
Waiting for response from server stdout...