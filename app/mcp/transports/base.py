"""
Base transport class for MCP server communications.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional

class Transport(ABC):
    """
    Abstract base class for MCP transports.
    
    Transports handle the communication layer between MCP clients and the server,
    providing message passing and serialization/deserialization.
    """
    
    def __init__(self):
        """Initialize the transport."""
        self._message_handler: Optional[Callable[[str, str], Optional[str]]] = None
    
    def set_message_handler(self, handler: Callable[[str, str], Optional[str]]) -> None:
        """
        Set the message handler function.
        
        Args:
            handler: A callable that takes a message string and transport ID,
                    and returns an optional response string
        """
        self._message_handler = handler
    
    @abstractmethod
    def start(self) -> None:
        """Start the transport."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the transport."""
        pass
    
    @abstractmethod
    def send_message(self, message: str) -> None:
        """
        Send a message to the client.
        
        Args:
            message: The message to send
        """
        pass