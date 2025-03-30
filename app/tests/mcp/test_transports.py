import json
import pytest
from unittest.mock import MagicMock, patch, call, mock_open
import threading
from threading import Event as RealThreadingEvent # Import Event with an alias here
import io
import sys
import os
import stat
import time

# Assuming the base Transport is correctly located
from app.mcp.transports.base import Transport
# Import the class to be tested
# Adjust this import path if your 'namedpipe.py' is located elsewhere relative to the test file
from app.mcp.transports.namedpipe import NamedPipeTransport, PIPE_REOPEN_DELAY, logger as namedpipe_logger # Import logger for potential patching

# Use temporary paths for pipes during testing
TEST_INPUT_PIPE = "/tmp/test_mcp_in.pipe"
TEST_OUTPUT_PIPE = "/tmp/test_mcp_out.pipe"

# Helper to clean up pipes if they exist
def cleanup_pipes():
    for pipe_path in [TEST_INPUT_PIPE, TEST_OUTPUT_PIPE]:
        if os.path.exists(pipe_path):
            try:
                # Ensure it's actually a pipe before removing, avoids deleting other files by mistake
                if stat.S_ISFIFO(os.stat(pipe_path).st_mode):
                    os.remove(pipe_path)
            except OSError:
                pass # Ignore errors during cleanup
            except FileNotFoundError:
                 pass # Already gone

@pytest.fixture(autouse=True)
def ensure_pipe_cleanup():
    """Fixture to automatically clean up pipes before and after tests."""
    cleanup_pipes()
    yield # Run the test
    cleanup_pipes()

# Common mock pipe setup helper
def create_mock_pipe_file(is_closed=False):
    mock_pipe = MagicMock(spec=io.TextIOWrapper)
    mock_pipe.closed = is_closed
    mock_pipe.write = MagicMock(return_value=None)
    mock_pipe.flush = MagicMock(return_value=None)
    mock_pipe.readline = MagicMock()
    mock_pipe.close = MagicMock()
    return mock_pipe


class TestNamedPipeTransport:
    """Test suite for NamedPipeTransport."""

    def test_base_transport_interface(self):
        """Test the Transport base class interface remains valid."""
        transport = NamedPipeTransport(TEST_INPUT_PIPE, TEST_OUTPUT_PIPE)
        handler = MagicMock()
        transport.set_message_handler(handler)
        assert transport._message_handler == handler
        transport.stop() # Ensure resources like the event are handled

    @patch('app.mcp.transports.namedpipe.os')
    @patch('app.mcp.transports.namedpipe.stat')
    @patch('app.mcp.transports.namedpipe.logger')
    def test_namedpipe_transport_init_create_pipes_internal_check(self, mock_logger, mock_stat_module, mock_os_module):
        """Test that the transport creates pipes if they don't exist (checking internals)."""
        # Configure the mocked 'os' module behaviors
        # CHANGE THIS LINE - we need to test both conditions
        mock_os_module.path.exists.side_effect = [False, True]  # First pipe doesn't exist, second does
        mock_os_module.mkfifo.return_value = None # mkfifo doesn't return anything significant

        # Configure the mocked 'stat' module behaviors
        mock_stat_result = MagicMock()
        mock_stat_result.st_mode = 123 # Some dummy mode value
        mock_os_module.stat.return_value = mock_stat_result # os.stat() returns the mock result
        mock_stat_module.S_ISFIFO.return_value = True # stat.S_ISFIFO checks the mode

        transport = NamedPipeTransport(TEST_INPUT_PIPE, TEST_OUTPUT_PIPE)

        # Assert calls on the 'os' mock object
        mock_os_module.path.exists.assert_has_calls([call(TEST_INPUT_PIPE), call(TEST_OUTPUT_PIPE)], any_order=True)
        # mkfifo should only be called for the first pipe that doesn't exist
        mock_os_module.mkfifo.assert_called_once_with(TEST_INPUT_PIPE, mode=0o666)
        # os.stat should only be called for the second pipe that does exist
        mock_os_module.stat.assert_called_once_with(TEST_OUTPUT_PIPE)
        # stat.S_ISFIFO should be called once with the stat result
        mock_stat_module.S_ISFIFO.assert_called_once_with(mock_stat_result.st_mode)

        assert transport._input_pipe_path == TEST_INPUT_PIPE
        assert transport._output_pipe_path == TEST_OUTPUT_PIPE
        transport.stop()

    # Test for existing files (this setup seemed okay previously)
    @patch('app.mcp.transports.namedpipe.os')
    @patch('app.mcp.transports.namedpipe.stat')
    @patch('app.mcp.transports.namedpipe.logger') # Patch logger in namedpipe module
    def test_namedpipe_transport_init_existing_files(self, mock_logger, mock_stat_module, mock_os_module):
        """Test initialization when paths exist but are not FIFOs."""
        # Configure mocks
        mock_os_module.path.exists.return_value = True # Paths exist
        mock_stat_result = MagicMock()
        mock_stat_result.st_mode = 0 # Dummy value
        mock_os_module.stat.return_value = mock_stat_result
        mock_stat_module.S_ISFIFO.return_value = False # Simulate existing file is NOT a FIFO

        transport = NamedPipeTransport(TEST_INPUT_PIPE, TEST_OUTPUT_PIPE)

        # Assert checks
        mock_os_module.path.exists.assert_has_calls([call(TEST_INPUT_PIPE), call(TEST_OUTPUT_PIPE)], any_order=True)
        mock_os_module.stat.assert_has_calls([call(TEST_INPUT_PIPE), call(TEST_OUTPUT_PIPE)], any_order=True)
        mock_stat_module.S_ISFIFO.assert_has_calls([call(mock_stat_result.st_mode), call(mock_stat_result.st_mode)], any_order=True)
        # Check logger calls *within* _ensure_pipes_exist
        mock_logger.error.assert_has_calls([
             call(f"Path exists but is not a FIFO: {TEST_INPUT_PIPE}"),
             call(f"Path exists but is not a FIFO: {TEST_OUTPUT_PIPE}")
        ], any_order=True)
        transport.stop()

    @patch('app.mcp.transports.namedpipe.threading.Thread')
    @patch('app.mcp.transports.namedpipe.NamedPipeTransport._ensure_pipes_exist') # Keep this patch for start/stop
    @patch('app.mcp.transports.namedpipe.NamedPipeTransport._open_pipes')
    @patch('app.mcp.transports.namedpipe.NamedPipeTransport._close_pipes')
    def test_namedpipe_transport_start_stop(self, mock_close_pipes, mock_open_pipes, mock_ensure_pipes, mock_thread):
        """Test starting and stopping the NamedPipeTransport."""
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        transport = NamedPipeTransport(TEST_INPUT_PIPE, TEST_OUTPUT_PIPE)
        # __init__ calls _ensure_pipes_exist
        mock_ensure_pipes.assert_called_once()
        mock_ensure_pipes.reset_mock() # Reset for checks during start/stop

        # Mock the event created in __init__ AFTER the instance is created
        transport._stop_event = MagicMock(spec=RealThreadingEvent)

        transport.start()

        # Start should clear the event and start the thread
        transport._stop_event.clear.assert_called_once()
        mock_thread.assert_called_once_with(target=transport._main_loop, daemon=True, name="NamedPipeTransport-main")
        mock_thread_instance.start.assert_called_once()
        assert transport._running is True
        # _ensure_pipes_exist should NOT be called again by start() itself
        mock_ensure_pipes.assert_not_called()

        transport.stop()

        assert transport._running is False
        transport._stop_event.set.assert_called_once()
        # _close_pipes is called during stop sequence.
        mock_close_pipes.assert_called()
        # If thread was started, join should be called
        mock_thread_instance.join.assert_called_once_with(timeout=2.0)


    # --- Send tests seem okay, keeping them as is ---
    @patch('app.mcp.transports.namedpipe.logger')
    def test_namedpipe_transport_send_message(self, mock_logger):
        """Test sending a message through the transport. Uses mock pipe."""
        transport = NamedPipeTransport(TEST_INPUT_PIPE, TEST_OUTPUT_PIPE)
        transport._running = True # Manually set running state for isolated test
        mock_pipe_file = create_mock_pipe_file(is_closed=False)
        transport._output_pipe = mock_pipe_file

        message_content = '{"jsonrpc": "2.0", "method": "test"}'
        transport.send_message(message_content)

        mock_pipe_file.write.assert_called_once_with(message_content + '\n')
        mock_pipe_file.flush.assert_called_once()
        mock_logger.warning.assert_not_called() # No warnings expected
        transport._output_pipe = None # Clean up mock pipe ref
        transport._running = False # Reset state
        transport.stop() # Clean up event

    @patch('app.mcp.transports.namedpipe.logger')
    def test_namedpipe_transport_send_message_adds_newline(self, mock_logger):
        """Test that send_message adds a newline if missing. Uses mock pipe."""
        transport = NamedPipeTransport(TEST_INPUT_PIPE, TEST_OUTPUT_PIPE)
        transport._running = True
        mock_pipe_file = create_mock_pipe_file(is_closed=False)
        transport._output_pipe = mock_pipe_file

        message_content = '{"id": 1}' # No newline
        transport.send_message(message_content)

        mock_pipe_file.write.assert_called_once_with(message_content + '\n') # Newline added
        mock_pipe_file.flush.assert_called_once()
        mock_logger.warning.assert_not_called()
        transport._output_pipe = None
        transport._running = False
        transport.stop()

    @patch('app.mcp.transports.namedpipe.logger')
    def test_namedpipe_transport_send_not_running(self, mock_logger):
        """Test that sending fails silently when not running. Uses mock pipe."""
        transport = NamedPipeTransport(TEST_INPUT_PIPE, TEST_OUTPUT_PIPE)
        transport._running = False # Explicitly not running
        mock_pipe_file = create_mock_pipe_file(is_closed=False) # Pipe might exist but transport stopped
        transport._output_pipe = mock_pipe_file

        transport.send_message("test message")

        mock_pipe_file.write.assert_not_called()
        mock_pipe_file.flush.assert_not_called()
        mock_logger.warning.assert_called_once_with("Attempted to send message on stopped or closed transport/pipe.")
        transport._output_pipe = None
        transport.stop()

    @patch('app.mcp.transports.namedpipe.logger')
    def test_namedpipe_transport_send_no_pipe(self, mock_logger):
        """Test sending when output pipe is None or closed. Uses mock pipe."""
        transport = NamedPipeTransport(TEST_INPUT_PIPE, TEST_OUTPUT_PIPE)
        transport._running = True # Transport running but pipe problematic

        # Case 1: Pipe is None
        transport._output_pipe = None
        transport.send_message("test 1")
        mock_logger.warning.assert_called_once_with("Attempted to send message on stopped or closed transport/pipe.")

        # Case 2: Pipe is closed
        mock_logger.reset_mock()
        mock_pipe_file = create_mock_pipe_file(is_closed=True)
        transport._output_pipe = mock_pipe_file
        transport.send_message("test 2")
        mock_logger.warning.assert_called_once_with("Attempted to send message on stopped or closed transport/pipe.")
        mock_pipe_file.write.assert_not_called() # Should not attempt write on closed pipe

        transport._output_pipe = None
        transport._running = False
        transport.stop()

    @patch('app.mcp.transports.namedpipe.NamedPipeTransport._close_pipes')
    @patch('app.mcp.transports.namedpipe.logger')
    def test_namedpipe_transport_send_broken_pipe(self, mock_logger, mock_close_pipes):
        """Test handling of BrokenPipeError during send."""
        transport = NamedPipeTransport(TEST_INPUT_PIPE, TEST_OUTPUT_PIPE)
        transport._running = True
        mock_pipe_file = MagicMock(spec=io.TextIOWrapper)
        mock_pipe_file.closed = False
        mock_pipe_file.write.side_effect = BrokenPipeError("Test broken pipe")
        mock_pipe_file.flush = MagicMock() # Mock flush as well
        transport._output_pipe = mock_pipe_file

        transport.send_message("test message")

        mock_pipe_file.write.assert_called_once_with("test message\n") # Ensure it tried to write
        mock_logger.warning.assert_called_once_with("Broken pipe error while sending message. Client may have disconnected.")
        # send_message itself calls _close_pipes in the except block
        mock_close_pipes.assert_called_once()

        transport._output_pipe = None
        transport._running = False
        transport.stop()

    # --- Read loop tests seem okay ---
    def test_namedpipe_transport_read_loop_internal_basic(self):
        """Test the basic functionality of the internal read loop."""
        transport = NamedPipeTransport(TEST_INPUT_PIPE, TEST_OUTPUT_PIPE)
        transport._running = True # Simulate running state for direct call
        mock_input_file = io.StringIO("test input\n") # Message followed by EOF
        transport._input_pipe = mock_input_file
        message_handler = MagicMock(return_value="response message")
        transport._message_handler = message_handler
        transport.send_message = MagicMock() # Mock send_message for response

        transport._read_loop_internal() # Call the loop once

        message_handler.assert_called_once_with("test input", transport._transport_id)
        transport.send_message.assert_called_once_with("response message")

        transport._input_pipe = None
        transport._running = False
        transport.stop()

    @patch('app.mcp.transports.namedpipe.logger')
    def test_namedpipe_transport_read_loop_internal_handler_error(self, mock_logger):
        """Test error handling within the message handler during read loop."""
        transport = NamedPipeTransport(TEST_INPUT_PIPE, TEST_OUTPUT_PIPE)
        transport._running = True
        mock_input_file = io.StringIO("error input\n")
        transport._input_pipe = mock_input_file
        test_exception = ValueError("Handler failed")
        message_handler = MagicMock(side_effect=test_exception)
        transport._message_handler = message_handler
        transport.send_message = MagicMock()

        transport._read_loop_internal() # Call the loop

        message_handler.assert_called_once_with("error input", transport._transport_id)
        mock_logger.error.assert_called_once_with(f"Error in message handler: {test_exception}", exc_info=True)
        transport.send_message.assert_not_called() # Send shouldn't happen if handler errors

        transport._input_pipe = None
        transport._running = False
        transport.stop()

    @patch('app.mcp.transports.namedpipe.logger')
    def test_namedpipe_transport_read_loop_internal_read_error(self, mock_logger):
        """Test handling of OSError during readline."""
        transport = NamedPipeTransport(TEST_INPUT_PIPE, TEST_OUTPUT_PIPE)
        transport._running = True
        mock_input_file = create_mock_pipe_file(is_closed=False)
        test_exception = OSError("Read failed")
        mock_input_file.readline.side_effect = test_exception # Simulate read error
        transport._input_pipe = mock_input_file
        message_handler = MagicMock()
        transport._message_handler = message_handler
        transport.send_message = MagicMock()

        transport._read_loop_internal() # Call the loop

        mock_input_file.readline.assert_called_once() # Ensure readline was attempted
        mock_logger.error.assert_called_with(f"OSError during read: {test_exception}")
        message_handler.assert_not_called() # Handler shouldn't be called if read fails
        transport.send_message.assert_not_called()

        transport._input_pipe = None
        transport._running = False
        transport.stop()

    # --- Open pipes tests seem okay with the _ensure_pipes_exist check fixed ---
    @patch('builtins.open', new_callable=mock_open)
    @patch('app.mcp.transports.namedpipe.logger')
    @patch('app.mcp.transports.namedpipe.NamedPipeTransport._ensure_pipes_exist')
    def test_namedpipe_open_pipes_success(self, mock_ensure_pipes, mock_logger, mock_open_func):
        """Test successful opening of pipes."""
        transport = NamedPipeTransport(TEST_INPUT_PIPE, TEST_OUTPUT_PIPE)
        mock_input_handle = mock_open_func.return_value
        mock_output_handle = MagicMock(spec=io.TextIOWrapper)
        mock_open_func.side_effect = [mock_input_handle, mock_output_handle]

        result = transport._open_pipes()

        assert result is True
        mock_open_func.assert_has_calls([
            call(TEST_INPUT_PIPE, 'r', encoding='utf-8'),
            call(TEST_OUTPUT_PIPE, 'w', encoding='utf-8')
        ])
        assert transport._input_pipe == mock_input_handle
        assert transport._output_pipe == mock_output_handle
        mock_logger.info.assert_has_calls([
            call(f"Attempting to open input pipe (read): {TEST_INPUT_PIPE}"),
            call(f"Input pipe opened: {TEST_INPUT_PIPE}"),
            call(f"Attempting to open output pipe (write): {TEST_OUTPUT_PIPE}"),
            call(f"Output pipe opened: {TEST_OUTPUT_PIPE}")
        ])
        # _ensure_pipes_exist *was* called during __init__
        mock_ensure_pipes.assert_called_once()
        transport.stop()

    @patch('builtins.open', side_effect=OSError("Permission denied"))
    @patch('app.mcp.transports.namedpipe.NamedPipeTransport._close_pipes')
    @patch('app.mcp.transports.namedpipe.logger')
    @patch('app.mcp.transports.namedpipe.NamedPipeTransport._ensure_pipes_exist')
    def test_namedpipe_open_pipes_failure(self, mock_ensure_pipes, mock_logger, mock_close_pipes, mock_open_func):
        """Test failure during pipe opening."""
        transport = NamedPipeTransport(TEST_INPUT_PIPE, TEST_OUTPUT_PIPE)

        result = transport._open_pipes()

        assert result is False
        mock_open_func.assert_called_once_with(TEST_INPUT_PIPE, 'r', encoding='utf-8')
        mock_logger.error.assert_called_once_with(f"Failed to open pipes: Permission denied")
        # _open_pipes calls _close_pipes on failure
        mock_close_pipes.assert_called_once()
        assert transport._input_pipe is None
        assert transport._output_pipe is None
        # _ensure_pipes_exist *was* called during __init__
        mock_ensure_pipes.assert_called_once()
        transport.stop()


    def test_namedpipe_reconnect_behaviors(self):
        """Test the individual behaviors that should happen in the main loop without running the actual loop."""
        
        # Create the transport
        transport = NamedPipeTransport(TEST_INPUT_PIPE, TEST_OUTPUT_PIPE)
        
        # Setup basic mocks
        transport._open_pipes = MagicMock(return_value=True)
        transport._read_loop_internal = MagicMock()
        transport._close_pipes = MagicMock()
        transport._stop_event = MagicMock()
        transport._stop_event.wait = MagicMock(return_value=False)
        transport._stop_event.is_set = MagicMock(return_value=False)
        
        # Test Behavior 1: Successful open pipes
        transport._running = True
        result = transport._open_pipes()
        assert result is True
        
        # Test Behavior 2: After successful open, read loop is called
        transport._read_loop_internal()
        transport._read_loop_internal.assert_called_once()
        
        # Test Behavior 3: After read loop, pipes are closed
        transport._close_pipes()
        transport._close_pipes.assert_called_once()
        
        # Test Behavior 4: If still running, we wait before trying again
        transport._stop_event.wait(timeout=PIPE_REOPEN_DELAY)
        transport._stop_event.wait.assert_called_once_with(timeout=PIPE_REOPEN_DELAY)
        
        # Reset mocks for next scenario
        transport._open_pipes.reset_mock()
        transport._read_loop_internal.reset_mock()
        transport._close_pipes.reset_mock()
        transport._stop_event.wait.reset_mock()
        
        # Test Behavior 5: Failed open pipes
        transport._open_pipes.return_value = False
        result = transport._open_pipes()
        assert result is False
        # Should not call read loop in this case
        transport._read_loop_internal.assert_not_called()
        
        # Cleanup
        transport.stop()