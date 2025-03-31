# mcp_server.py
import logging
import sys
import os
import signal
import asyncio

from app.mcp.server import MCPServer
from app.mcp.transports import StdioTransport
from app.models.query_engine import CyberneticsQueryEngine

# Setup logging (as before)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
DATA_FILE = os.getenv("CYBERON_DATA_PATH", "app/data/cybernetics_ontology.json")

# --- Global Server Instance ---
# Consider if a global is the best approach, but keep for consistency for now
server = None
shutdown_event = asyncio.Event() # Use an asyncio event for shutdown

async def main(): # Make main asynchronous
    global server
    logger.info("Starting CYBERON MCP Server...")

    # --- Initialize Server ---
    server = MCPServer()

    query_engine = None
    if os.path.exists(DATA_FILE):
        try:
            query_engine = CyberneticsQueryEngine(DATA_FILE)
            server.set_query_engine(query_engine)
            logger.info(f"Query engine loaded from {DATA_FILE}")
        except Exception as e:
            logger.error(f"Failed to load query engine from {DATA_FILE}: {e}")
    else:
        logger.error(f"Data file not found: {DATA_FILE}")
        logger.warning("Running without query engine - some functionality will be limited")

    # --- Initialize Transport ---
    stdio_transport = StdioTransport()

    # --- Configure Transport BEFORE async with ---
    # The server knows its own message handler
    stdio_transport.set_message_handler(server.handle_message)

    # --- Register Transport with Server (gets ID) ---
    # Server manages the mapping, transport doesn't need the ID *yet*
    transport_id = server.register_transport(stdio_transport)
    logger.info(f"StdioTransport registered with ID: {transport_id}")

    # --- Run the transport using async with ---
    try:
        logger.info("Entering StdioTransport async context...")
        async with stdio_transport as transport: # Calls __aenter__, starts reader loop task
            # --- Activate Transport INSIDE async with ---
            # Now that __aenter__ has run, call start to provide the ID
            # The reader loop might be waiting for this ID.
            transport.start(transport_id)
            # transport object here is the same as stdio_transport

            logger.info(f"StdioTransport [{transport_id}] is active. Server ready.")

            # Keep the server running
            await shutdown_event.wait()
            logger.info(f"Shutdown signal received, exiting StdioTransport context...")

    except Exception as e:
        logger.error(f"Error during StdioTransport execution: {e}", exc_info=True)
    finally:
        logger.info("StdioTransport context finished.")

def handle_shutdown_signal(sig, frame):
    logger.warning(f"Received signal {sig}, initiating shutdown...")
    # Set the asyncio event to stop the main loop waiting
    shutdown_event.set()

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown_signal) # Handle Ctrl+C
    signal.signal(signal.SIGTERM, handle_shutdown_signal) # Handle termination signals

    try:
        # Run the main async function using asyncio.run()
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt caught in main block, shutting down.")
    except Exception as e:
        logger.exception("Unhandled exception in main execution block.")
    finally:
        logger.info("MCP Server main process finished.")