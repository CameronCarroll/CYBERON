# simple_client.py
"""
Simplified MCP Debug Client using basic file I/O for named pipes.

This script sends a single JSON-RPC request and reads a single response,
printing exactly what is sent and received. Useful for debugging pipe/server issues.
"""

import json
import sys
import os
import time

# --- Configuration ---
# Adjust these paths to match where your named pipes are
PIPE_IN_PATH = "/run/cyberon/mcp_in.pipe"   # Client writes here (Server reads)
PIPE_OUT_PATH = "/run/cyberon/mcp_out.pipe" # Client reads here (Server writes)

# --- Choose ONE request to send ---
# 1. Initialize Request
request_payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "client_info": {
            "name": "Simple Debug Client",
            "version": "0.0.1"
        }
    }
}

# # 2. Capabilities Request (Uncomment to use this instead)
# request_payload = {
#     "jsonrpc": "2.0",
#     "id": 2,
#     "method": "server/capabilities",
#     "params": {}
# }

# # 3. Search Request (Uncomment to use this instead - requires prior init)
# request_payload = {
#     "jsonrpc": "2.0",
#     "id": 3,
#     "method": "cyberon/search",
#     "params": { "query": "bayesian", "limit": 3 }
# }

# --- Script Logic ---

def main():
    print(f"--- Simple MCP Debug Client ---")
    print(f"Attempting to use pipes:")
    print(f"  Write to (Server Reads): {PIPE_IN_PATH}")
    print(f"  Read from (Server Writes): {PIPE_OUT_PATH}")

    # Convert request payload to JSON string
    try:
        request_json = json.dumps(request_payload)
    except TypeError as e:
        print(f"ERROR: Failed to serialize request payload: {e}")
        sys.exit(1)

    # Ensure pipes exist
    if not os.path.exists(PIPE_IN_PATH):
        print(f"ERROR: Input pipe not found: {PIPE_IN_PATH}")
        sys.exit(1)
    if not os.path.exists(PIPE_OUT_PATH):
        print(f"ERROR: Output pipe not found: {PIPE_OUT_PATH}")
        sys.exit(1)

    pipe_out_handle = None
    pipe_in_handle = None

    try:
        # --- Open Pipes ---
        print("Opening pipes (this might block if server isn't ready)...")
        # Open the pipe the server reads from for writing FIRST
        pipe_out_handle = open(PIPE_IN_PATH, 'w')
        print(f"Opened {PIPE_IN_PATH} for writing.")
        # Open the pipe the server writes to for reading SECOND
        pipe_in_handle = open(PIPE_OUT_PATH, 'r')
        print(f"Opened {PIPE_OUT_PATH} for reading.")
        print("-" * 20)

        # --- Send Request ---
        print(f"SENDING JSON >>>\n{request_json}\n" + "-"*20)
        # Write the request JSON, MUST end with a newline for readline() on server
        pipe_out_handle.write(request_json + '\n')
        # MUST flush to ensure it's sent through the pipe immediately
        pipe_out_handle.flush()
        print("Flushed output pipe.")

        # --- Receive Response ---
        print("Waiting for response (reading line from input pipe)...")
        # Read one line from the pipe the server writes to
        # This will block until the server writes a line ending with '\n'
        response_json = pipe_in_handle.readline()
        print("-" * 20)

        if not response_json:
            print("RECEIVED EOF <<< (End of File - Pipe closed by server?)")
        else:
            # Strip potential trailing newline
            response_json = response_json.strip()
            print(f"RECEIVED JSON <<<\n{response_json}\n" + "-"*20)

            # Optional: Try to parse the response JSON
            try:
                response_data = json.loads(response_json)
                print("Response parsed successfully.")
                # You could add checks here, e.g., if 'error' in response_data: ...
            except json.JSONDecodeError as e:
                print(f"WARNING: Received invalid JSON: {e}")

    except IOError as e:
        print(f"\nERROR: Pipe I/O Error: {e}")
        print("Check if server is running and pipe permissions are correct.")
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred: {e}")
    finally:
        # --- Close Pipes ---
        print("-" * 20)
        if pipe_out_handle:
            try:
                pipe_out_handle.close()
                print(f"Closed {PIPE_IN_PATH}")
            except Exception as e:
                 print(f"Error closing {PIPE_IN_PATH}: {e}")
        if pipe_in_handle:
            try:
                pipe_in_handle.close()
                print(f"Closed {PIPE_OUT_PATH}")
            except Exception as e:
                 print(f"Error closing {PIPE_OUT_PATH}: {e}")
        print("--- Debug Client Finished ---")


if __name__ == "__main__":
    main()