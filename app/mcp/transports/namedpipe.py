import sys
import json
import threading
import logging
import os
import stat
import time
from typing import Optional, IO

# Assuming 'Transport' is defined in this path based on the original import
from app.mcp.transports.base import Transport 

logger = logging.getLogger(__name__)

# Default paths (consider making these configurable)
DEFAULT_INPUT_PIPE_PATH = "/run/cyberon/mcp_in.pipe"
DEFAULT_OUTPUT_PIPE_PATH = "/run/cyberon/mcp_out.pipe"
PIPE_REOPEN_DELAY = 1 # Seconds to wait before trying to reopen pipes after EOF

class NamedPipeTransport(Transport):
    """
    Named Pipe-based transport for the MCP server.

    This transport communicates via two named pipes (FIFOs),
    one for input and one for output. It's designed for persistent
    server operation, handling client connections and disconnections.
    """

    def __init__(self, 
                 input_pipe_path: str = DEFAULT_INPUT_PIPE_PATH, 
                 output_pipe_path: str = DEFAULT_OUTPUT_PIPE_PATH):
        """
        Initialize the Named Pipe transport.

        Args:
            input_pipe_path: Filesystem path for the input named pipe (server reads).
            output_pipe_path: Filesystem path for the output named pipe (server writes).
        """
        super().__init__()
        self._running = False
        self._read_thread: Optional[threading.Thread] = None
        self._transport_id = f"named_pipe:{os.getpid()}" # Unique ID per instance

        self._input_pipe_path = input_pipe_path
        self._output_pipe_path = output_pipe_path

        self._input_pipe: Optional[IO[str]] = None
        self._output_pipe: Optional[IO[str]] = None
        
        # Ensure pipes exist (optional, depends on setup)
        self._ensure_pipes_exist()

        self._stop_event = threading.Event() # Used to signal thread termination

    def _ensure_pipes_exist(self) -> None:
        """Create named pipes if they don't exist."""
        for pipe_path in [self._input_pipe_path, self._output_pipe_path]:
            if not os.path.exists(pipe_path):
                try:
                    os.mkfifo(pipe_path, mode=0o666)
                    logger.info(f"Created named pipe: {pipe_path}")
                except OSError as e:
                    logger.error(f"Failed to create named pipe {pipe_path}: {e}")
                    # Decide if this is fatal? For now, log and continue.
            elif not stat.S_ISFIFO(os.stat(pipe_path).st_mode):
                 logger.error(f"Path exists but is not a FIFO: {pipe_path}")
                 # This is likely a fatal configuration error.

    def _open_pipes(self) -> bool:
        """
        Open the named pipes for communication. Handles blocking.
        Returns True if pipes were opened successfully, False otherwise.
        """
        # Open pipes in a specific order to avoid deadlock in some scenarios.
        # Server typically waits for client to connect (write to input, read from output).
        # Opening input pipe (read) will block until a writer connects.
        # Opening output pipe (write) may block until a reader connects.

        logger.info(f"Attempting to open input pipe (read): {self._input_pipe_path}")
        try:
            # Open input pipe first (blocks until client opens for write)
            self._input_pipe = open(self._input_pipe_path, 'r', encoding='utf-8')
            logger.info(f"Input pipe opened: {self._input_pipe_path}")
            
            # Then open output pipe (may block until client opens for read)
            logger.info(f"Attempting to open output pipe (write): {self._output_pipe_path}")
            self._output_pipe = open(self._output_pipe_path, 'w', encoding='utf-8')
            logger.info(f"Output pipe opened: {self._output_pipe_path}")
            
            return True
            
        except OSError as e:
            logger.error(f"Failed to open pipes: {e}")
            self._close_pipes() # Ensure cleanup if one opened but the other failed
            return False
        except Exception as e:
             logger.error(f"Unexpected error opening pipes: {e}", exc_info=True)
             self._close_pipes()
             return False

    def _close_pipes(self) -> None:
        """Close the named pipes."""
        if self._input_pipe:
            try:
                self._input_pipe.close()
                logger.debug(f"Input pipe closed: {self._input_pipe_path}")
            except Exception as e:
                logger.warning(f"Error closing input pipe: {e}")
            finally:
                self._input_pipe = None # Ensure it's marked as closed

        if self._output_pipe:
            try:
                self._output_pipe.close()
                logger.debug(f"Output pipe closed: {self._output_pipe_path}")
            except Exception as e:
                logger.warning(f"Error closing output pipe: {e}")
            finally:
                 self._output_pipe = None # Ensure it's marked as closed


    def start(self) -> None:
        """
        Start the transport.
        
        Opens the named pipes and starts the read loop in a background thread.
        Handles reconnections if the client disconnects.
        """
        if self._running:
            logger.warning("Transport already running.")
            return

        logger.info("Starting NamedPipeTransport...")
        self._running = True
        self._stop_event.clear() # Reset stop event

        self._read_thread = threading.Thread(
            target=self._main_loop, # Changed target to a new main loop
            daemon=True,
            name="NamedPipeTransport-main"
        )
        self._read_thread.start()
        logger.info("NamedPipeTransport started.")

    def stop(self) -> None:
        """Stop the transport."""
        if not self._running:
            logger.info("NamedPipeTransport already stopped.")
            return

        logger.info("Stopping NamedPipeTransport...")
        self._running = False
        self._stop_event.set() # Signal the main loop to stop

        # Closing the pipes from here can help unblock the read loop thread
        # if it's stuck waiting for I/O.
        self._close_pipes() 

        if self._read_thread and self._read_thread.is_alive():
            logger.debug("Waiting for transport thread to join...")
            self._read_thread.join(timeout=2.0)
            if self._read_thread.is_alive():
                 logger.warning("Transport thread did not join cleanly.")
        
        self._read_thread = None
        logger.info("NamedPipeTransport stopped.")

    def send_message(self, message: str) -> None:
        """
        Send a message to the client via the output pipe.

        Args:
            message: The JSON RPC message string to send.
        """
        if not self._running or not self._output_pipe or self._output_pipe.closed:
            logger.warning("Attempted to send message on stopped or closed transport/pipe.")
            return

        try:
            # Ensure message ends with a newline for readline() compatibility
            if not message.endswith('\n'):
                message += '\n'
                
            self._output_pipe.write(message)
            self._output_pipe.flush() # Crucial for pipes
            logger.debug(f"Sent message: {message.strip()}") # Log stripped message
            
        except BrokenPipeError:
            # Client likely disconnected
            logger.warning("Broken pipe error while sending message. Client may have disconnected.")
            # Optionally: trigger pipe closing/reopening logic here or let the read loop handle it via EOF
            self._close_pipes() # Close pipes immediately on broken pipe
        except OSError as e:
            logger.error(f"OSError sending message: {e}")
            self._close_pipes() # Assume connection is lost
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}", exc_info=True)
            self._close_pipes() # Assume connection is lost


    def _main_loop(self) -> None:
        """
        Main loop that handles pipe opening and reading.
        Will attempt to reopen pipes if the client disconnects (EOF).
        """
        while self._running:
            if not self._open_pipes():
                 # Failed to open pipes, maybe they don't exist or permissions issue
                 logger.error("Failed to open pipes. Waiting before retry...")
                 time.sleep(PIPE_REOPEN_DELAY) # Wait before retrying
                 continue # Retry opening

            logger.info("Pipes opened successfully. Starting read loop.")
            self._read_loop_internal() # Start processing messages

            # If _read_loop_internal exits, it means EOF or error occurred
            logger.info("Read loop exited. Closing pipes.")
            self._close_pipes()

            if self._running:
                 # If we are still supposed to be running, wait before trying to reopen
                 logger.info(f"Client disconnected or pipe error. Waiting {PIPE_REOPEN_DELAY}s before accepting new connection...")
                 # Use the stop event for waiting to allow quick shutdown
                 self._stop_event.wait(timeout=PIPE_REOPEN_DELAY) 
            
            # Loop continues if self._running is still True

        logger.info("NamedPipeTransport main loop finished.")


    def _read_loop_internal(self) -> None:
        """
        Internal loop that reads messages from the input pipe.
        This runs only when pipes are successfully opened.
        Exits on EOF or critical read error.
        """
        assert self._input_pipe is not None # Should be guaranteed by _main_loop

        while self._running:
            try:
                line = self._input_pipe.readline()

                if not line:
                    # EOF received - Client closed its writing end of the pipe
                    logger.info("Received EOF on input pipe. Client disconnected.")
                    break # Exit this inner loop to trigger pipe closing/reopening

                message = line.rstrip('\n')
                if not message:
                    logger.debug("Received empty line, skipping.")
                    continue

                logger.debug(f"Received message: {message}")
                if self._message_handler:
                    try:
                        response = self._message_handler(message, self._transport_id)
                        if response:
                            self.send_message(response)
                    except Exception as e:
                         logger.error(f"Error in message handler: {e}", exc_info=True)
                         # Decide if we should send an error response back?
                         # For now, just log it.
                else:
                    logger.warning("Received message but no handler is registered.")

            except ValueError as e:
                # Can happen if reading from a closed pipe
                if "I/O operation on closed file" in str(e):
                    logger.warning("Attempted to read from a closed input pipe.")
                else:
                    logger.error(f"ValueError during read: {e}", exc_info=True)
                break # Exit loop on error
            except OSError as e:
                 logger.error(f"OSError during read: {e}")
                 break # Exit loop on error
            except Exception as e:
                logger.error(f"Unexpected error in read loop: {e}", exc_info=True)
                # Optional: add a small delay here to prevent tight error loops
                time.sleep(0.1) 
                # Continue vs Break? Let's break for safety, assuming pipe state is unknown
                break 
                
        logger.debug("Exiting internal read loop.")