# mcp_test_client.py
"""
Test client for MCP Server using subprocess communication (stdin/stdout).

This script launches the MCP server, sends a single JSON-RPC request via
the server's stdin, reads a single response from the server's stdout,
and prints detailed, colorful debug information.
"""

import json
import sys
import os
import time
import subprocess
import threading
import signal # For better termination

# --- Configuration ---

# IMPORTANT: Path to the server script RELATIVE TO WHERE YOU RUN THIS CLIENT
# or an absolute path.
SERVER_SCRIPT_PATH = "mcp_server.py" # <--- CHANGE THIS if server.py is elsewhere

# Path to the python executable to use for the server
# Uses the same python that's running this script by default.
PYTHON_EXECUTABLE = sys.executable

# Choose ONE request to send by uncommenting it:
# 1. Initialize Request
request_payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "client_info": {
            "name": "Subprocess Test Client",
            "version": "1.0.0"
        }
    }
}

# # 2. Capabilities Request (Requires server to handle it without prior init)
# request_payload = {
#     "jsonrpc": "2.0",
#     "id": 2,
#     "method": "server/capabilities",
#     "params": {}
# }

# # 3. Search Request (Requires server to handle it, likely needs prior init)
# request_payload = {
#     "jsonrpc": "2.0",
#     "id": 3,
#     "method": "cyberon/search",
#     "params": { "query": "graph database", "limit": 2 }
# }

# --- Terminal Colors (ANSI escape codes) ---
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_MAGENTA = "\033[95m"
COLOR_CYAN = "\033[96m"
COLOR_BOLD = "\033[1m"

# --- Helper Functions ---

def print_color(text, color=COLOR_RESET, bold=False, **kwargs):
    """Prints text in a specific color."""
    prefix = f"{COLOR_BOLD}" if bold else ""
    print(f"{prefix}{color}{text}{COLOR_RESET}", **kwargs)

def print_divider(char='*', length=70, color=COLOR_CYAN, design='sparkle'):
    """Prints a decorative divider."""
    if design == 'sparkle':
        pattern = f" {char} sparkly {char} "
    elif design == 'rocket':
        pattern = " 🚀 "
    elif design == 'dashed':
        pattern = f"{char}--"
    elif design == 'dots':
        pattern = f".{char}."
    else: # simple
        pattern = char
    
    full_line = (pattern * (length // len(pattern) + 1))[:length]
    print_color(full_line, color)

def read_stream(stream, prefix, color):
    """Reads lines from a stream (like stderr) and prints them."""
    try:
        for line in iter(stream.readline, ''):
            print_color(f"{prefix}: {line.strip()}", color, file=sys.stderr)
    except Exception as e:
        print_color(f"{prefix} Stream Read Error: {e}", COLOR_RED, file=sys.stderr)
    finally:
        print_color(f"{prefix} Stream Closed.", color, file=sys.stderr)


# --- Main Script Logic ---

def main():
    print_divider(char='✨', design='sparkle', color=COLOR_MAGENTA)
    print_color("--- MCP Subprocess Test Client ---", COLOR_MAGENTA, bold=True)
    print_divider(char='✨', design='sparkle', color=COLOR_MAGENTA)

    # --- Validate Server Path ---
    if not os.path.exists(SERVER_SCRIPT_PATH):
        print_color(f"ERROR: Server script not found at: {SERVER_SCRIPT_PATH}", COLOR_RED)
        print_color(f"Please update SERVER_SCRIPT_PATH in the script.", COLOR_YELLOW)
        sys.exit(1)
    print_color(f"Using server script: {os.path.abspath(SERVER_SCRIPT_PATH)}", COLOR_CYAN)
    print_color(f"Using python: {PYTHON_EXECUTABLE}", COLOR_CYAN)

    # --- Prepare Request ---
    try:
        request_json = json.dumps(request_payload)
    except TypeError as e:
        print_color(f"ERROR: Failed to serialize request payload: {e}", COLOR_RED)
        sys.exit(1)

    server_process = None
    stderr_thread = None

    try:
        # --- Launch Server Subprocess ---
        print_divider(char='🚀', design='rocket', color=COLOR_BLUE)
        print_color("Launching MCP server process...", COLOR_BLUE, bold=True)

        # We use text=True for automatic encoding/decoding (usually utf-8)
        # bufsize=1 means line-buffered output
        server_process = subprocess.Popen(
            [PYTHON_EXECUTABLE, SERVER_SCRIPT_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Ensures strings are used for I/O
            encoding='utf-8', # Explicit encoding
            bufsize=1 # Line buffering for stdout/stderr
        )

        print_color(f"Server process launched (PID: {server_process.pid}).", COLOR_GREEN)

        # --- Start Thread to Read Server's stderr ---
        # This prevents the stderr buffer from filling up and blocking the server
        stderr_thread = threading.Thread(
            target=read_stream,
            args=(server_process.stderr, "[Server STDERR]", COLOR_YELLOW),
            daemon=True # Allows script to exit even if thread is running
        )
        stderr_thread.start()
        print_color("Started thread to monitor server stderr.", COLOR_CYAN)
        time.sleep(0.5) # Give server a moment to start up if needed

        print_divider(char='>', length=70, color=COLOR_GREEN, design='dashed')
        print_color("SENDING JSON >>>", COLOR_GREEN, bold=True)
        print_color(request_json, COLOR_GREEN)
        print_divider(char='>', length=70, color=COLOR_GREEN, design='dashed')

        # --- Send Request to Server's stdin ---
        # Add newline! Server likely uses readline()
        server_process.stdin.write(request_json + '\n')
        server_process.stdin.flush() # Ensure data is sent
        print_color("Flushed server stdin.", COLOR_CYAN)

        # Close stdin to signal EOF to the server. Some servers might wait
        # for stdin to close before processing the last input.
        server_process.stdin.close()
        print_color("Closed server stdin.", COLOR_CYAN)


        # --- Receive Response from Server's stdout ---
        print_divider(char='<', length=70, color=COLOR_MAGENTA, design='dashed')
        print_color("Waiting for response from server stdout...", COLOR_MAGENTA, bold=True)

        # Read one line from the server's output
        # This will block until the server writes a line ending with '\n' or closes stdout
        response_json = server_process.stdout.readline()
        print_divider(char='<', length=70, color=COLOR_MAGENTA, design='dashed')


        if not response_json:
            print_color("RECEIVED EOF <<< (End of File)", COLOR_YELLOW, bold=True)
            print_color("Server might have exited or closed stdout without sending data.", COLOR_YELLOW)
            # Check if process exited unexpectedly
            ret_code = server_process.poll()
            if ret_code is not None:
                 print_color(f"Server process exited early with code: {ret_code}", COLOR_RED)
            response_data = None
        else:
            # Strip potential trailing newline
            response_json = response_json.strip()
            print_color("RECEIVED JSON <<<", COLOR_MAGENTA, bold=True)
            print_color(response_json, COLOR_MAGENTA)
            print_divider(char='.', length=70, color=COLOR_MAGENTA, design='dots')

            # Optional: Try to parse the response JSON
            try:
                response_data = json.loads(response_json)
                print_color("Response parsed successfully.", COLOR_GREEN)
                # Example check:
                if isinstance(response_data, dict) and response_data.get("error"):
                    print_color("Server returned an error:", COLOR_YELLOW)
                    print_color(json.dumps(response_data["error"], indent=2), COLOR_YELLOW)
            except json.JSONDecodeError as e:
                print_color(f"WARNING: Received invalid JSON: {e}", COLOR_YELLOW)
                print_color(f"Raw data received: '{response_json}'", COLOR_YELLOW)


    except FileNotFoundError:
        print_color(f"ERROR: Python executable not found at: {PYTHON_EXECUTABLE}", COLOR_RED)
        print_color(f"Or server script not found relative to execution: {SERVER_SCRIPT_PATH}", COLOR_RED)
    except BrokenPipeError:
         print_color(f"ERROR: Broken pipe. Server process likely exited unexpectedly.", COLOR_RED)
         ret_code = server_process.poll() if server_process else 'N/A'
         print_color(f"Server exit code (if available): {ret_code}", COLOR_RED)
    except Exception as e:
        print_color(f"\nERROR: An unexpected error occurred: {type(e).__name__} - {e}", COLOR_RED)
        import traceback
        traceback.print_exc()

    finally:
        # --- Cleanup ---
        print_divider(char='🧹', design='rocket', color=COLOR_BLUE)
        print_color("Cleaning up...", COLOR_BLUE, bold=True)

        if server_process:
            print_color(f"Attempting to terminate server process (PID: {server_process.pid})...", COLOR_CYAN)
            if server_process.poll() is None: # Check if still running
                try:
                    # Try graceful termination first
                    print_color("Sending SIGTERM...", COLOR_YELLOW)
                    server_process.terminate()
                    try:
                        # Wait a short time for graceful shutdown
                        server_process.wait(timeout=2)
                        print_color("Server terminated gracefully.", COLOR_GREEN)
                    except subprocess.TimeoutExpired:
                        print_color("Server did not terminate gracefully, sending SIGKILL...", COLOR_RED)
                        server_process.kill()
                        server_process.wait(timeout=1) # Wait for kill
                        print_color("Server killed.", COLOR_YELLOW)

                except Exception as term_err:
                    print_color(f"Error during server termination: {term_err}", COLOR_RED)

            # Get final exit code
            exit_code = server_process.poll()
            print_color(f"Server process final exit code: {exit_code}", COLOR_CYAN)

            # Ensure streams are closed (though Popen context manager usually handles this)
            try: server_process.stdout.close()
            except: pass
            try: server_process.stderr.close()
            except: pass

        # Wait for the stderr reader thread to finish processing any remaining output
        if stderr_thread and stderr_thread.is_alive():
            print_color("Waiting for stderr monitor thread to finish...", COLOR_CYAN)
            stderr_thread.join(timeout=1.0) # Wait briefly
            if stderr_thread.is_alive():
                 print_color("Stderr monitor thread still alive after join.", COLOR_YELLOW)

        print_divider(char='🏁', design='rocket', color=COLOR_MAGENTA)
        print_color("--- Test Client Finished ---", COLOR_MAGENTA, bold=True)
        print_divider(char='🏁', design='rocket', color=COLOR_MAGENTA)


if __name__ == "__main__":
    main()