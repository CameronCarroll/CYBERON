# File: app/mcp/transports/stdio.py

import sys
import logging
import anyio
import asyncio
import json
from typing import Callable, Optional, TypeVar, Generic, Any, Mapping

# Ensure direct import from anyio.streams.text
from anyio.streams.text import TextReceiveStream, TextSendStream
from anyio.abc import ByteReceiveStream, ByteSendStream
from .base import Transport, MessageType  # Assuming base.py is in the same directory

logger = logging.getLogger(__name__)

# For StdioTransport, the MessageType will be string (raw JSON)
StrMessageType = str

class StdinByteStream(ByteReceiveStream):
    """Adapts a standard IO buffer to the anyio ByteReceiveStream interface."""
    
    def __init__(self, buffer):
        self._buffer = buffer
        self._closed = False
    
    async def receive(self) -> bytes:
        """Read a line from stdin as bytes."""
        if self._closed:
            raise anyio.ClosedResourceError("Stream is closed")
            
        # Run blocking read in a thread pool
        try:
            line = await anyio.to_thread.run_sync(self._buffer.readline)
            if not line:  # EOF
                self._closed = True
                raise anyio.EndOfStream()
            return line
        except Exception as e:
            logger.error(f"Error reading from stdin: {e}")
            self._closed = True
            raise anyio.EndOfStream() from e
    
    async def aclose(self) -> None:
        """Mark the stream as closed."""
        self._closed = True
        # We don't actually close stdin
    
    @property
    def extra_attributes(self) -> Mapping[Any, Callable[[], Any]]:
        """Return any extra attributes for the stream."""
        return {}

class StdoutByteStream(ByteSendStream):
    """Adapts a standard IO buffer to the anyio ByteSendStream interface."""
    
    def __init__(self, buffer):
        self._buffer = buffer
        self._closed = False
    
    async def send(self, item: bytes) -> None:
        """Write bytes to stdout and flush."""
        if self._closed:
            raise anyio.ClosedResourceError("Stream is closed")
            
        try:
            # Write and flush in a thread pool
            await anyio.to_thread.run_sync(self._send_and_flush, item)
        except Exception as e:
            logger.error(f"Error writing to stdout: {e}")
            self._closed = True
            raise anyio.BrokenResourceError("Failed to write to stdout") from e
    
    def _send_and_flush(self, data: bytes) -> None:
        """Synchronous helper to write and flush."""
        self._buffer.write(data)
        self._buffer.flush()
    
    async def aclose(self) -> None:
        """Mark the stream as closed."""
        self._closed = True
        # We don't actually close stdout
    
    @property
    def extra_attributes(self) -> Mapping[Any, Callable[[], Any]]:
        """Return any extra attributes for the stream."""
        return {}

class StdioTransport(Transport[StrMessageType]):
    """
    MCP Transport implementation using standard input/output (stdio).

    Assumes line-delimited JSON messages. Reads from stdin and writes to stdout.
    Uses anyio for asynchronous operations.
    """

    def __init__(self):
        # Use correct type hints from direct import
        self._receive_stream: Optional[TextReceiveStream] = None
        self._send_stream: Optional[TextSendStream] = None
        self._message_handler: Optional[Callable[[StrMessageType, str], Optional[StrMessageType]]] = None
        self._transport_id: Optional[str] = None
        # _reader_task is managed by the task group, don't store separately
        self._task_group: Optional[anyio.abc.TaskGroup] = None
        self._closed: bool = True
        self._stop_event: Optional[anyio.Event] = None # Use anyio.Event

    def set_message_handler(self, handler: Callable[[StrMessageType, str], Optional[StrMessageType]]):
        """Sets the callback function to handle incoming messages."""
        self._message_handler = handler

    async def _reader_loop(self):
        """Background task to read messages from stdin and pass them to the handler."""

        # Wait for essential state
        while self._message_handler is None or self._transport_id is None:
            if self._closed or (self._stop_event and self._stop_event.is_set()):
                logger.warning(f"StdioTransport reader loop terminating before activation due to transport closure/stop signal.")
                return
            logger.debug("StdioTransport reader loop waiting for handler and transport ID...")
            await anyio.sleep(0.05)

        # Capture local vars
        transport_id = self._transport_id
        message_handler = self._message_handler
        receive_stream = self._receive_stream
        stop_event = self._stop_event

        if not receive_stream or not message_handler or not transport_id or not stop_event:
            logger.error("StdioTransport reader loop failed initialization check even after waiting.")
            return

        logger.info(f"StdioTransport [{transport_id}] reader loop activated and starting.")
        try:
            # Loop while not closed and stop not signaled
            while not self._closed and not stop_event.is_set():
                try:
                    # --- Simplified Read ---
                    # Block here until a line is received, EOF, or error
                    logger.debug(f"StdioTransport [{transport_id}] waiting to receive...")
                    message = await receive_stream.receive()
                    logger.debug(f"StdioTransport [{transport_id}] receive() returned.")

                    # TextReceiveStream usually strips newline and raises EndOfStream
                    # If message is None or empty string for any reason, log and continue
                    if message is None: # Defensive check
                         logger.warning(f"StdioTransport [{transport_id}] receive() returned None, skipping.")
                         await anyio.sleep(0.01) # Avoid tight loop if stream behaves oddly
                         continue
                    if not message: # Empty line received (e.g., user just pressed Enter)
                        logger.debug(f"StdioTransport [{transport_id}] received empty line, skipping.")
                        continue

                    # --- Process Message ---
                    logger.debug(f"StdioTransport [{transport_id}] received: {message[:100]}{'...' if len(message) > 100 else ''}")
                    try:
                        response = message_handler(message, transport_id)
                        if response:
                            await self.send(response)
                    except Exception as handler_exc:
                         logger.exception(f"StdioTransport [{transport_id}] error in message handler for message: {message[:100]}")
                         # Continue processing next message unless error is critical

                except anyio.EndOfStream:
                    logger.info(f"StdioTransport [{transport_id}] input stream closed (EOF).")
                    break # Exit loop cleanly
                except anyio.ClosedResourceError:
                    logger.warning(f"StdioTransport [{transport_id}] receive stream closed unexpectedly.")
                    break # Exit loop
                except Exception as receive_exc:
                    # Handle unexpected errors during receive/processing
                    logger.exception(f"StdioTransport [{transport_id}] error receiving/processing message: {receive_exc}")
                    # Break the loop on unknown errors for safety
                    break

                # --- Yield control ---
                # Give other tasks a chance to run after successfully processing a message.
                # This is important for responsiveness and shutdown handling.
                await anyio.sleep(0)

        except Exception as task_exc:
             logger.exception(f"StdioTransport [{transport_id}] reader task encountered an unhandled error: {task_exc}")
        finally:
            logger.info(f"StdioTransport [{transport_id}] reader loop finished.")
            # Ensure transport is closed if the reader stops unexpectedly
            if not self._closed:
                 await self.close()


    # --- Transport ABC Implementation ---

    async def receive(self) -> StrMessageType:
        """
        Receive the next complete message.

        Note: In this implementation, messages are primarily handled by the
        background reader loop and the message_handler callback. This method
        might not be directly used by the MCPServer structure provided,
        but is implemented for completeness of the Transport interface.
        """
        if self._closed or not self._receive_stream:
             raise anyio.ClosedResourceError("StdioTransport is closed.")

        logger.warning("StdioTransport.receive() called directly, which may not be intended with the callback model.")
        try:
            # TextReceiveStream handles decoding and should strip newlines
            line = await self._receive_stream.receive()
            # Defensive stripping, though TextReceiveStream should handle it.
            return line.strip() # <-- Added strip() here
        except anyio.EndOfStream:
             logger.info("Stdio input stream closed during direct receive call.")
             await self.close() # Close transport if EOF reached on direct call
             raise
        except anyio.ClosedResourceError:
             logger.warning("Stdio stream closed during direct receive call.")
             # Already closed, ensure state is consistent
             self._closed = True
             raise

    async def send(self, message: StrMessageType) -> None:
        """Send a message to stdout."""
        if self._closed or not self._send_stream:
            raise anyio.ClosedResourceError("StdioTransport is closed.")

        logger.debug(f"StdioTransport [{self._transport_id}] sending: {message[:100]}{'...' if len(message) > 100 else ''}")
        try:
            # TextSendStream handles encoding and requires newline for line separation
            if not message.endswith('\n'):
                message += '\n'
            await self._send_stream.send(message)
        except (anyio.BrokenResourceError, anyio.ClosedResourceError) as e:
             logger.error(f"StdioTransport [{self._transport_id}] stdout pipe broken or closed: {e}. Closing transport.")
             await self.close() # Ensure closed on send error
             # Re-raise as ClosedResourceError for consistency upstream
             raise anyio.ClosedResourceError(f"Stdio output broken or closed: {e}") from e
        except Exception as e:
             logger.exception(f"StdioTransport [{self._transport_id}] error sending message: {e}")
             # Depending on the error, we might want to close here too
             # For now, just raise the original exception
             raise

    async def __aenter__(self) -> 'StdioTransport':
        """Enter the async context, setting up stdio streams and the reader task."""
        logger.debug("Entering StdioTransport async context.")
        if not self._closed:
             logger.warning("StdioTransport __aenter__ called on an already active transport.")
             return self

        self._task_group = None # Ensure task group is reset
        try:
            # Create proper byte stream wrappers that implement receive/send
            stdin_stream = StdinByteStream(sys.stdin.buffer)
            stdout_stream = StdoutByteStream(sys.stdout.buffer)

            # Create text streams with explicit UTF-8 encoding and error handling
            # Use the correctly imported classes
            self._receive_stream = TextReceiveStream(stdin_stream)
            self._send_stream = TextSendStream(stdout_stream)

            self._stop_event = anyio.Event()
            self._task_group = anyio.create_task_group()
            await self._task_group.__aenter__() # Enter task group context

            self._closed = False # Mark as open *before* starting reader

            # Start the background reader task IF a message handler is set
            # Defer starting if no handler is set? No, server sets handler later. Start always.
            # Server needs to call set_message_handler before messages arrive
            self._task_group.start_soon(self._reader_loop)
            logger.info("StdioTransport activated and reader task started.")

        except Exception as e:
             logger.exception("Failed to initialize StdioTransport streams or task group.")
             # Ensure cleanup if initialization fails
             if self._task_group and hasattr(self._task_group, '_active') and self._task_group._active: # Check if TG context entered
                  await self._task_group.__aexit__(*sys.exc_info())
             if self._send_stream: await self._send_stream.aclose()
             if self._receive_stream: await self._receive_stream.aclose()
             self._closed = True
             self._task_group = None
             self._receive_stream = None
             self._send_stream = None
             raise

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context, ensuring resources are cleaned up."""
        logger.debug(f"Exiting StdioTransport async context (exc_type: {exc_type}).")
        await self.close()
         # Task group cleanup is handled within close()

    async def close(self) -> None:
        """Explicitly close the transport connection and clean up resources."""
        # Check if already closed at the start and return early if true
        if self._closed:
            logger.debug(f"StdioTransport [{self._transport_id}] close() called but already closed.")
            return

        logger.info(f"StdioTransport [{self._transport_id}] closing...")
        self._closed = True # Mark as closed immediately
        
        # Store local copies of references before nullifying them
        stop_event = self._stop_event
        task_group = self._task_group
        receive_stream = self._receive_stream
        send_stream = self._send_stream
        
        # Clear all references immediately to ensure idempotence on subsequent calls
        self._stop_event = None
        self._task_group = None
        self._receive_stream = None
        self._send_stream = None

        # 1. Signal the reader loop to stop if event exists
        if stop_event:
             stop_event.set() # Event.set() is synchronous

        # 2. Cancel and wait for the task group (which includes the reader loop)
        if task_group:
            task_group.cancel_scope.cancel() # CancelScope.cancel() is synchronous
            # Exiting the task group's context waits for tasks
            # Need proper error handling for __aexit__ here
            exc_info = sys.exc_info() if sys.exc_info() != (None, None, None) else (None, None, None)
            try:
                # Check if task group context is still active before exiting
                logger.debug(f"StdioTransport [{self._transport_id}] exiting task group...")
                if await task_group.__aexit__(*exc_info):
                     # If __aexit__ returns True, an exception was suppressed
                     logger.warning(f"StdioTransport [{self._transport_id}] task group suppressed an exception during close.")
                logger.debug(f"StdioTransport [{self._transport_id}] task group exited.")
            except Exception as e:
                 logger.exception(f"StdioTransport [{self._transport_id}] Error occurred while closing task group: {e}")

        # 3. Close the streams (safely)
        if send_stream:
            try:
                await send_stream.aclose()
                logger.debug(f"StdioTransport [{self._transport_id}] send stream closed.")
            except Exception as e:
                logger.exception(f"StdioTransport [{self._transport_id}] Error closing send stream: {e}")

        if receive_stream:
            try:
                await receive_stream.aclose()
                logger.debug(f"StdioTransport [{self._transport_id}] receive stream closed.")
            except Exception as e:
                logger.exception(f"StdioTransport [{self._transport_id}] Error closing receive stream: {e}")

        logger.info(f"StdioTransport [{self._transport_id}] closed successfully.")

    def is_closed(self) -> bool:
        """Check if the transport connection is closed."""
        return self._closed

    # --- Methods called by MCPServer ---

    def start(self, transport_id: str):
        """
        Marks the transport as started and assigns its ID.

        In this implementation, the main setup happens in __aenter__.
        This method primarily sets the ID needed for the message handler.
        It assumes __aenter__ has already been successfully called.
        """
        if self._closed:
             logger.error(f"Attempted to start StdioTransport [{transport_id}] but it's not active (use async with).")
             raise RuntimeError("StdioTransport must be started using 'async with'.")
        if not self._receive_stream or not self._send_stream or not self._task_group:
             logger.error(f"Attempted to start StdioTransport [{transport_id}] but streams/TG not initialized (likely __aenter__ failed or wasn't called).")
             raise RuntimeError("StdioTransport internal state inconsistent on start().")

        self._transport_id = transport_id
        logger.info(f"StdioTransport [{self._transport_id}] started and ready.")

    async def stop(self):
        """
        Initiates the closing process.

        Now an async method that simply calls close() directly.
        """
        logger.info(f"StdioTransport [{self._transport_id}] received stop request.")
        if not self._closed:
            await self.close()