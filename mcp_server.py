#!/usr/bin/env python
"""
MCP Server entry point for CYBERON.

This script initializes and starts the MCP server for CYBERON,
providing Model Context Protocol integration.
"""

import sys
import os
import argparse
import logging
import signal
from typing import Optional

from app.mcp import MCPServer
from app.models.query_engine import CyberneticsQueryEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger("mcp_server")

# Global server instance for signal handlers
server_instance: Optional[MCPServer] = None

def signal_handler(sig, frame):
    """Handle signals to gracefully shutdown the server."""
    if server_instance:
        logger.info(f"Received signal {sig}, shutting down...")
        server_instance.stop()
    sys.exit(0)

def load_query_engine(data_file: str) -> Optional[CyberneticsQueryEngine]:
    """
    Load the CyberneticsQueryEngine from a data file.
    
    Args:
        data_file: Path to the data file
        
    Returns:
        Query engine instance or None if loading fails
    """
    try:
        if not os.path.exists(data_file):
            logger.error(f"Data file not found: {data_file}")
            return None
        
        logger.info(f"Loading query engine from {data_file}")
        engine = CyberneticsQueryEngine(data_file)
        logger.info(f"Query engine loaded with {engine.graph.number_of_nodes()} nodes and {engine.graph.number_of_edges()} edges")
        return engine
    except Exception as e:
        logger.exception(f"Error loading query engine: {e}")
        return None

def main():
    """Main entry point for the MCP server."""
    global server_instance
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="CYBERON MCP Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--transport", default="stdio", choices=["stdio"], help="Transport to use")
    parser.add_argument("--data-file", default="data/cybernetics_ontology.json", 
                        help="Path to the ontology data file")
    args = parser.parse_args()
    
    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start the server
    try:
        logger.info("Initializing MCP server")
        server = MCPServer()
        server_instance = server
        
        # Initialize and set up the query engine
        data_file = os.path.abspath(args.data_file)
        query_engine = load_query_engine(data_file)
        
        if query_engine:
            server.set_query_engine(query_engine)
        else:
            logger.warning("Running without query engine - some functionality will be limited")
        
        # Set up the requested transport
        if args.transport == "stdio":
            logger.info("Using STDIO transport")
            server.create_stdio_transport()
        
        # Start the server
        logger.info("Starting MCP server")
        server.start()
        
        # For STDIO transport, the server will run in background threads
        # and we need to keep the main thread alive
        if args.transport == "stdio":
            # Use signal.pause() to wait for signals on Unix systems
            if hasattr(signal, 'pause'):
                signal.pause()
            else:
                # On Windows or other platforms without signal.pause()
                import time
                while True:
                    time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        if server_instance:
            server_instance.stop()
    except Exception as e:
        logger.exception(f"Error running MCP server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())