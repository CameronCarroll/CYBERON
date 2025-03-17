"""
STDIO transport implementation for MCP server.

This module provides a transport that communicates with clients via
standard input and output streams, making it suitable for local
process communication.
"""

import sys
import json
import threading
import logging
from typing import Optional

from app.mcp.transports.base import Transport

logger = logging.getLogger(__name__)

class StdioTransport(Transport):
    """
    STDIO-based transport for the MCP server.
    
    This transport uses standard input and output streams for
    communication, making it suitable for local process communication
    where the client has spawned the server as a child process.
    """
    
    def __init__(self):
        """Initialize the STDIO transport."""
        super().__init__()
        self._running = False
        self._read_thread = None
        self._transport_id = "stdio"
        
        # Configure stdio
        self._configure_stdio()
    
    def _configure_stdio(self) -> None:
        """Configure standard input and output for proper binary communication."""
        # In Python 3, stdin/stdout are already in binary mode if needed
        # For STDIO transport, we use text mode
        if hasattr(sys.stdin, 'reconfigure'):
            sys.stdin.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    
    def start(self) -> None:
        """Start the transport, beginning to listen for messages on stdin."""
        if self._running:
            return
        
        self._running = True
        self._read_thread = threading.Thread(
            target=self._read_loop,
            daemon=True,
            name="StdioTransport-read"
        )
        self._read_thread.start()
        logger.info("STDIO transport started")
    
    def stop(self) -> None:
        """Stop the transport."""
        self._running = False
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=1.0)
        logger.info("STDIO transport stopped")
    
    def send_message(self, message: str) -> None:
        """
        Send a message to the client via stdout.
        
        Args:
            message: The message to send
        """
        if not self._running:
            logger.warning("Attempted to send message on stopped transport")
            return
        
        try:
            # Format the message according to jsonrpc specification over stdio
            print(message, flush=True)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    def _read_loop(self) -> None:
        """Read messages from stdin and pass them to the message handler."""
        while self._running:
            try:
                # Read a line from stdin
                line = sys.stdin.readline()
                
                # Check if we've reached EOF
                if not line:
                    logger.info("Reached EOF on stdin, stopping transport")
                    self._running = False
                    break
                
                # Trim trailing newline if present
                line = line.rstrip('\n')
                
                # Skip empty lines
                if not line:
                    continue
                
                # Process the message if we have a handler
                if self._message_handler:
                    response = self._message_handler(line, self._transport_id)
                    if response:
                        self.send_message(response)
                else:
                    logger.warning("Received message but no handler is registered")
                    
            except Exception as e:
                logger.error(f"Error in read loop: {e}")
                
                # Try to send an error response
                if self._message_handler:
                    try:
                        error_response = json.dumps({
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": {
                                "code": -32603,
                                "message": "Internal error",
                                "data": str(e)
                            }
                        })
                        self.send_message(error_response)
                    except Exception:
                        pass  # If we can't send the error, there's not much we can do