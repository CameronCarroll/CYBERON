# src/client_main.cr
#
# Test client for MCP Server using subprocess communication (stdin/stdout).
#
# This script launches the MCP server, sends a single JSON-RPC request via
# the server's stdin, reads a single response from the server's stdout,
# and prints detailed, colorful debug information.

require "./mcp_client"
require "./transport"
require "./errors"
require "log"
require "json"
require "option_parser"

# --- Configuration ---
SERVER_SCRIPT_PATH = "../mcp_server.py" # Default path, relative to where this is run
REQUEST_TYPE       = "initialize"       # Default request type

# Terminal Colors (ANSI escape codes)
COLOR_RESET   = "\033[0m"
COLOR_RED     = "\033[91m"
COLOR_GREEN   = "\033[92m"
COLOR_YELLOW  = "\033[93m"
COLOR_BLUE    = "\033[94m"
COLOR_MAGENTA = "\033[95m"
COLOR_CYAN    = "\033[96m"
COLOR_BOLD    = "\033[1m"

# Command line options
server_path = SERVER_SCRIPT_PATH
request_type = REQUEST_TYPE
log_level = Log::Severity::Info
use_shell = false

# Parse command line options
OptionParser.parse do |parser|
  parser.banner = "Usage: client_main [options]"

  parser.on("-s SERVER", "--server=SERVER", "Path to the MCP server script") do |path|
    server_path = path
  end

  parser.on("-r REQUEST", "--request=REQUEST", "Request type (initialize, capabilities, search)") do |req|
    request_type = req
  end

  parser.on("-v", "--verbose", "Enable verbose logging") do
    log_level = Log::Severity::Debug
  end

  parser.on("-S", "--shell", "Run server command in shell") do
    use_shell = true
  end

  parser.on("-h", "--help", "Show this help") do
    puts parser
    exit
  end
end

# --- Helper Functions ---
def print_color(text, color = COLOR_RESET, bold = false)
  prefix = bold ? COLOR_BOLD : ""
  puts "#{prefix}#{color}#{text}#{COLOR_RESET}"
end

def print_divider(char = '*', length = 70, color = COLOR_CYAN, design = "sparkle")
  pattern = case design
            when "sparkle"
              " #{char} sparkly #{char} "
            when "rocket"
              " 🚀 "
            when "dashed"
              "#{char}--"
            when "dots"
              ".#{char}."
            else # simple
              char
            end

  full_line = (pattern * (length // pattern.size + 1))[0...length]
  print_color(full_line, color)
end

# Configure logging
Log.setup do |config|
  backend = Log::IOBackend.new

  config.bind("*", log_level, backend)
  config.bind("mcp_client", log_level, backend)
  config.bind("mcp_transport.*", log_level, backend)
end

# --- Create Request Payload ---
def create_request_payload(type : String) : Hash
  case type
  when "initialize", "init"
    {
      "jsonrpc" => "2.0",
      "id"      => 1,
      "method"  => "initialize",
      "params"  => {
        "client_info" => {
          "name"    => "Crystal Test Client",
          "version" => "1.0.0",
        },
      },
    }
  when "capabilities", "caps"
    {
      "jsonrpc" => "2.0",
      "id"      => 2,
      "method"  => "server/capabilities",
      "params"  => {} of String => String,
    }
  when "search"
    {
      "jsonrpc" => "2.0",
      "id"      => 3,
      "method"  => "cyberon/search",
      "params"  => {"query" => "graph database", "limit" => 2},
    }
  else
    print_color("Unknown request type: #{type}. Using initialize request.", COLOR_YELLOW)
    create_request_payload("initialize")
  end
end

# --- Main Script Logic ---
def main(server_path : String, request_type : String, use_shell : Bool)
  print_divider(char: '✨', design: "sparkle", color: COLOR_MAGENTA)
  print_color("--- MCP Crystal Test Client ---", COLOR_MAGENTA, bold: true)
  print_divider(char: '✨', design: "sparkle", color: COLOR_MAGENTA)

  # --- Validate Server Path ---
  unless File.exists?(server_path)
    print_color("ERROR: Server script not found at: #{server_path}", COLOR_RED)
    print_color("Please update --server option or SERVER_SCRIPT_PATH in the script.", COLOR_YELLOW)
    exit(1)
  end

  server_abs_path = File.expand_path(server_path)
  print_color("Using server script: #{server_abs_path}", COLOR_CYAN)

  # --- Prepare Request ---
  request_payload = create_request_payload(request_type)
  request_json = request_payload.to_json

  transport = nil
  client = nil

  begin
    # --- Launch Server Process ---
    print_divider(char: '🚀', design: "rocket", color: COLOR_BLUE)
    print_color("Launching MCP server process...", COLOR_BLUE, bold: true)

    transport = CyberonMCP::ProcessTransport.new(server_abs_path, use_shell)
    transport.launch_server

    print_color("Server process launched successfully.", COLOR_GREEN)

    # --- Send Request to Server ---
    print_divider(char: '>', length: 70, color: COLOR_GREEN, design: "dashed")
    print_color("SENDING JSON >>>", COLOR_GREEN, bold: true)
    print_color(request_json, COLOR_GREEN)
    print_divider(char: '>', length: 70, color: COLOR_GREEN, design: "dashed")

    # Create client and send request
    client = CyberonMCP::Client.new(transport)

    # --- Handle different request types
    response_data = nil

    case request_type
    when "initialize", "init"
      # The init_connection method handles both sending and receiving
      print_color("Initializing connection...", COLOR_CYAN)
      server_info = client.init_connection
      response_data = server_info
    when "capabilities", "caps"
      # Send capabilities request manually without init
      print_color("Sending capabilities request without initialization...", COLOR_CYAN)
      response = client.send_request("server/capabilities", {} of String => String)
      response_data = response
    when "search"
      # Try to search without init (may fail on some servers)
      print_color("Sending search request without initialization...", COLOR_CYAN)
      params = {"query" => "graph database", "limit" => 2}
      response = client.send_request("cyberon/search", params)
      response_data = response
    end

    # --- Receive Response from Server ---
    print_divider(char: '<', length: 70, color: COLOR_MAGENTA, design: "dashed")
    print_color("RECEIVED RESPONSE <<<", COLOR_MAGENTA, bold: true)

    if response_data.nil?
      print_color("No response data received!", COLOR_YELLOW)
    else
      response_json = response_data.to_json
      print_color(response_json, COLOR_MAGENTA)
      print_divider(char: '.', length: 70, color: COLOR_MAGENTA, design: "dots")

      # Check for errors in response
      if response_data.is_a?(Hash) && response_data.has_key?("error")
        print_color("Server returned an error:", COLOR_YELLOW)
        print_color(response_data["error"].to_json, COLOR_YELLOW)
      else
        print_color("Response received successfully.", COLOR_GREEN)
      end
    end
  rescue ex : IO::Error
    print_color("TRANSPORT ERROR: #{ex.message}", COLOR_RED)
  rescue ex : MCPRuntimeError | MCPValueError
    print_color("MCP ERROR: #{ex.message}", COLOR_RED)
  rescue ex : Exception
    print_color("UNEXPECTED ERROR: #{ex.class.name} - #{ex.message}", COLOR_RED)
    ex.backtrace.each do |line|
      STDERR.puts "  #{line}"
    end
  ensure
    # --- Cleanup ---
    print_divider(char: '🧹', design: "rocket", color: COLOR_BLUE)
    print_color("Cleaning up...", COLOR_BLUE, bold: true)

    if client && client.initialized?
      print_color("Shutting down connection...", COLOR_CYAN)
      begin
        client.shutdown
      rescue
        # Ignore shutdown errors
      end
    end

    if client
      print_color("Sending exit notification...", COLOR_CYAN)
      begin
        client.exit # This will also close the transport
      rescue ex
        print_color("Error during exit: #{ex.message}", COLOR_YELLOW)
      end
    elsif transport
      print_color("Closing transport...", COLOR_CYAN)
      begin
        transport.close
      rescue ex
        print_color("Error closing transport: #{ex.message}", COLOR_YELLOW)
      end
    end

    print_divider(char: '🏁', design: "rocket", color: COLOR_MAGENTA)
    print_color("--- Test Client Finished ---", COLOR_MAGENTA, bold: true)
    print_divider(char: '🏁', design: "rocket", color: COLOR_MAGENTA)
  end
end

# Run the main function
main(server_path, request_type, use_shell)
