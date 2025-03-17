"""
Tests for the MCP transport implementations.
"""

import json
import pytest
from unittest.mock import MagicMock, patch, call
import threading
import io
import sys

from app.mcp.transports.base import Transport
from app.mcp.transports.stdio import StdioTransport

class TestTransports:
    """Test suite for MCP transports."""
    
    def test_base_transport_interface(self):
        """Test the Transport base class interface."""
        # The Transport class is abstract, so we need to create a minimal implementation
        class MinimalTransport(Transport):
            def start(self): pass
            def stop(self): pass
            def send_message(self, message): pass
        
        # Create an instance
        transport = MinimalTransport()
        
        # Test setting a message handler
        handler = MagicMock()
        transport.set_message_handler(handler)
        assert transport._message_handler == handler
    
    @patch('sys.stdin')
    @patch('sys.stdout')
    def test_stdio_transport_configuration(self, mock_stdout, mock_stdin):
        """Test that the STDIO transport configures itself correctly."""
        # Mock the reconfigure method
        mock_stdin.reconfigure = MagicMock()
        mock_stdout.reconfigure = MagicMock()
        
        # Create the transport
        transport = StdioTransport()
        
        # Verify stdin/stdout were reconfigured
        mock_stdin.reconfigure.assert_called_once_with(encoding='utf-8', errors='replace')
        mock_stdout.reconfigure.assert_called_once_with(encoding='utf-8', errors='replace')
    
    @patch('app.mcp.transports.stdio.threading.Thread')
    def test_stdio_transport_start_stop(self, mock_thread):
        """Test starting and stopping the STDIO transport."""
        # Create a mock thread
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Create the transport
        transport = StdioTransport()
        
        # Start the transport
        transport.start()
        
        # Verify a thread was created and started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        assert transport._running is True
        
        # Stop the transport
        transport.stop()
        
        # Verify the transport was stopped
        assert transport._running is False
        mock_thread_instance.join.assert_called_once_with(timeout=1.0)
    
    @patch('app.mcp.transports.stdio.print')
    def test_stdio_transport_send_message(self, mock_print):
        """Test sending a message through the STDIO transport."""
        # Create the transport
        transport = StdioTransport()
        transport._running = True
        
        # Send a message
        transport.send_message("test message")
        
        # Verify the message was sent
        mock_print.assert_called_once_with("test message", flush=True)
    
    @patch('app.mcp.transports.stdio.print')
    def test_stdio_transport_not_running(self, mock_print):
        """Test that sending a message fails when the transport is not running."""
        # Create the transport
        transport = StdioTransport()
        transport._running = False
        
        # Send a message
        transport.send_message("test message")
        
        # Verify the message was not sent
        mock_print.assert_not_called()
    
    @patch('sys.stdin')
    def test_stdio_transport_read_loop_basic(self, mock_stdin):
        """Test the basic functionality of the read loop."""
        # Setup mock stdin with a sequence of inputs
        mock_stdin.readline.side_effect = ["test input\n", ""]
        
        # Create the transport
        transport = StdioTransport()
        transport._running = True
        
        # Set up a mock message handler
        message_handler = MagicMock(return_value="response")
        transport._message_handler = message_handler
        
        # Mock the send_message method
        transport.send_message = MagicMock()
        
        # Run the read loop
        transport._read_loop()
        
        # Verify the handler was called with the input
        message_handler.assert_called_once_with("test input", "stdio")
        
        # Verify the response was sent
        transport.send_message.assert_called_once_with("response")
        
        # Verify the transport is no longer running (due to EOF)
        assert transport._running is False
    
    @patch('sys.stdin')
    def test_stdio_transport_read_loop_error(self, mock_stdin):
        """Test error handling in the read loop."""
        # Setup mock stdin - make it return one line then stop the loop
        def mock_readline():
            if not hasattr(mock_readline, 'called'):
                mock_readline.called = True
                return "test input\n"
            else:
                # This will cause the loop to exit
                return ""  
        mock_stdin.readline.side_effect = mock_readline
        
        # Create the transport
        transport = StdioTransport()
        transport._running = True
        
        # Set up a message handler that raises an exception
        def failing_handler(message, transport_id):
            raise ValueError("Test error")
        
        transport._message_handler = failing_handler
        
        # Mock the send_message method
        transport.send_message = MagicMock()
        
        # Run the read loop - it should exit after the second readline
        transport._read_loop()
        
        # In the real implementation, the error handler should call send_message
        # to send an error response
        assert transport.send_message.call_count >= 1