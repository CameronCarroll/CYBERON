Mar 29 18:58:16 brill sh[202563]: 2025-03-29 18:58:16,017 - mcp_server - ERROR - Error in MCP server main execution: module 'posixpath' has no attribute 'is_fifo'
Mar 29 18:58:16 brill sh[202563]: Traceback (most recent call last):
Mar 29 18:58:16 brill sh[202563]:   File "/home/cam/repos/cyberon/mcp_server.py", line 102, in main
Mar 29 18:58:16 brill sh[202563]:     transport_id = server.create_namedpipe_transport() # Get ID just in case
Mar 29 18:58:16 brill sh[202563]:   File "/home/cam/repos/cyberon/app/mcp/server.py", line 163, in create_namedpipe_transport
Mar 29 18:58:16 brill sh[202563]:     transport = NamedPipeTransport()
Mar 29 18:58:16 brill sh[202563]:   File "/home/cam/repos/cyberon/app/mcp/transports/stdio.py", line 50, in __init__
Mar 29 18:58:16 brill sh[202563]:     self._ensure_pipes_exist()
Mar 29 18:58:16 brill sh[202563]:     ~~~~~~~~~~~~~~~~~~~~~~~~^^
Mar 29 18:58:16 brill sh[202563]:   File "/home/cam/repos/cyberon/app/mcp/transports/stdio.py", line 64, in _ensure_pipes_exist
Mar 29 18:58:16 brill sh[202563]:     elif not os.path.is_fifo(pipe_path):
Mar 29 18:58:16 brill sh[202563]:              ^^^^^^^^^^^^^^^
Mar 29 18:58:16 brill sh[202563]: AttributeError: module 'posixpath' has no attribute 'is_fifo'