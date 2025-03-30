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
        # Use stderr for critical debug prints, as stdout is the data pipe
        print("StdioTransport: _read_loop started.", file=sys.stderr, flush=True)
        loop_iteration = 0
        while self._running:
            loop_iteration += 1
            print(f"StdioTransport: _read_loop iteration {loop_iteration}, self._running={self._running}", file=sys.stderr, flush=True)
            try:
                print("StdioTransport: Attempting sys.stdin.readline()...", file=sys.stderr, flush=True)
                line = sys.stdin.readline()
                print(f"StdioTransport: sys.stdin.readline() returned '{line!r}'", file=sys.stderr, flush=True) # Show exactly what was read

                if not line:
                    print("StdioTransport: Read EOF on stdin, stopping loop.", file=sys.stderr, flush=True)
                    self._running = False # Ensure flag is set
                    break # Exit loop on EOF

                line = line.rstrip('\n')
                print(f"StdioTransport: Stripped line: '{line}'", file=sys.stderr, flush=True)

                if not line:
                    print("StdioTransport: Skipping empty line.", file=sys.stderr, flush=True)
                    continue

                print(f"StdioTransport: Processing line: '{line}'", file=sys.stderr, flush=True)
                if self._message_handler:
                    response = self._message_handler(line, self._transport_id)
                    if response:
                        print(f"StdioTransport: Handler returned response, calling send_message.", file=sys.stderr, flush=True)
                        self.send_message(response)
                    else:
                            print(f"StdioTransport: Handler returned no response.", file=sys.stderr, flush=True)
                else:
                    print("StdioTransport: No message handler registered.", file=sys.stderr, flush=True)
                    logger.warning("Received message but no handler is registered")

            except Exception as e:
                # Log exception details to stderr immediately
                import traceback
                print(f"StdioTransport: !!! EXCEPTION IN READ LOOP !!!", file=sys.stderr, flush=True)
                print(f"Error: {e}", file=sys.stderr, flush=True)
                traceback.print_exc(file=sys.stderr)
                print("StdioTransport: Setting self._running=False due to exception.", file=sys.stderr, flush=True)
                self._running = False
                break # Exit loop on unhandled exception

        print("StdioTransport: _read_loop finished.", file=sys.stderr, flush=True)