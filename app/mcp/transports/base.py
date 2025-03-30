import anyio
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

# Define a generic type for the messages the transport will handle.
# This would typically be a dict representing the parsed JSON-RPC message,
# or a more specific Pydantic/dataclass model.
MessageType = TypeVar("MessageType")

class Transport(Generic[MessageType], ABC):
    """
    Abstract base class for an MCP transport connection.

    This class represents a single, active communication channel (like an
    established stdio connection, a WebSocket connection, or an SSE stream pair).

    It acts as an async context manager to handle setup and teardown.
    It provides streams for sending and receiving structured messages
    (typically parsed JSON-RPC objects).
    """

    @abstractmethod
    async def receive(self) -> MessageType:
        """
        Receive the next complete message from the connected client.

        This method should handle reading raw data, message framing,
        deserialization (e.g., from JSON), and potentially validation.

        Returns:
            The next message received from the client.

        Raises:
            anyio.EndOfStream: If the connection is closed normally.
            Exception: For other receive errors (e.g., deserialization failure,
                       underlying connection error).
        """
        pass

    @abstractmethod
    async def send(self, message: MessageType) -> None:
        """
        Send a message to the connected client.

        This method should handle serialization (e.g., to JSON),
        message framing, and writing to the underlying communication channel.

        Args:
            message: The message object to send.

        Raises:
            Exception: For send errors (e.g., serialization failure,
                       underlying connection error).
        """
        pass

    # __aenter__ and __aexit__ are part of the AsyncContextManager protocol
    # Implementing them makes the class usable with 'async with'
    # Implementations will typically set up the connection in __aenter__
    # and tear it down in __aexit__.

    @abstractmethod
    async def __aenter__(self) -> 'Transport[MessageType]':
        """Enter the async context, typically establishing the connection."""
        # Example: Connect socket, open subprocess pipes
        # Implementation should return self or an appropriate context object
        return self # Default for abstract, implementations might override slightly

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the async context, ensuring resources are cleaned up."""
        # Implementation should handle cleanup
        # Example: Close socket, close pipes, wait for subprocess
        pass

    @abstractmethod
    async def close(self) -> None:
        """Explicitly close the transport connection."""
        pass
    
    @abstractmethod
    def is_closed(self) -> bool:
        """Check if the transport connection is closed."""
        pass