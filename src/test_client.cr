#!/usr/bin/env crystal
# src/test_client.cr
# A simple test client that launches the MCP server process and
# communicates with it using the ProcessTransport.

require "./mcp_client"
require "./transport"
require "./errors"
require "log"
require "option_parser"

# Configuration
SERVER_PATH = "./mcp_server.py"  # Default path, run from main dir
LOG_LEVEL = Log::Severity::Info

# Parse command line options
server_path = SERVER_PATH
log_level = LOG_LEVEL
use_shell = false

OptionParser.parse do |parser|
  parser.banner = "Usage: test_client [options]"
  
  parser.on("-s PATH", "--server=PATH", "Path to MCP server script") do |path|
    server_path = path
  end
  
  parser.on("-v", "--verbose", "Enable verbose logging") do
    log_level = Log::Severity::Debug
  end
  
  parser.on("-S", "--shell", "Run server in shell") do
    use_shell = true
  end
  
  parser.on("-h", "--help", "Show this help") do
    puts parser
    exit
  end
end

# Configure logging
Log.setup do |config|
  backend = Log::IOBackend.new
  config.bind("*", log_level, backend)
end

# --- Color constants for output formatting ---
COLOR_RESET  = "\033[0m"
COLOR_RED    = "\033[91m"
COLOR_GREEN  = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE   = "\033[94m"
COLOR_CYAN   = "\033[96m"
COLOR_MAGENTA = "\033[95m"
COLOR_BOLD   = "\033[1m"

def print_color(text, color = COLOR_RESET, bold = false)
  prefix = bold ? COLOR_BOLD : ""
  puts "#{prefix}#{color}#{text}#{COLOR_RESET}"
end

def print_divider(char = "*", length = 70, color = COLOR_CYAN)
  line = char * length
  print_color(line, color)
end

# --- Main script ---
begin
  # Find the absolute path to the server
  server_abs_path = File.expand_path(server_path)
  
  # Check if the server script exists
  unless File.exists?(server_abs_path)
    print_color("ERROR: Server script not found at: #{server_abs_path}", COLOR_RED)
    print_color("Please provide a valid server path with the --server option.", COLOR_YELLOW)
    exit(1)
  end
  
  print_divider("=", 70, COLOR_BLUE)
  print_color("CRYSTAL MCP TEST CLIENT", COLOR_BLUE, true)
  print_divider("=", 70, COLOR_BLUE)
  print_color("Server path: #{server_abs_path}", COLOR_CYAN)
  
  # Create the transport and launch the server
  print_color("Creating transport and launching server...", COLOR_CYAN)
  transport = CyberonMCP::ProcessTransport.new(server_abs_path, use_shell)
  transport.launch_server
  print_color("Server process launched successfully!", COLOR_GREEN)
  
  # Create the client
  print_color("Creating MCP client...", COLOR_CYAN)
  client = CyberonMCP::Client.new(transport, "Crystal Test Client", "1.0.0")
  
  # Initialize the connection
  print_color("Initializing connection...", COLOR_CYAN)
  server_info = client.init_connection
  print_color("Connection initialized successfully!", COLOR_GREEN)
  
  # Display server information
  print_divider("-", 70, COLOR_MAGENTA)
  print_color("SERVER INFO:", COLOR_MAGENTA, true)
  server_info_pretty = JSON.parse(server_info.to_json).to_pretty_json
  print_color(server_info_pretty, COLOR_MAGENTA)
  print_divider("-", 70, COLOR_MAGENTA)
  
  debugger

  # Try some requests based on capabilities
  if client.server_capabilities.dig?("cyberon", "search")
    print_color("Testing search functionality...", COLOR_CYAN)
    begin
      search_result = client.send_request("cyberon/search", {"query" => "test query", "limit" => 5})
      print_color("Search response:", COLOR_GREEN)
      print_color(search_result.to_json, COLOR_GREEN)
    rescue ex
      print_color("Error during search: #{ex.message}", COLOR_YELLOW)
    end
  end
  
  if client.server_capabilities.dig?("resources", "list")
    print_color("Testing resource listing...", COLOR_CYAN)
    begin
      resources_result = client.send_request("resources/list", {} of String => String)
      print_color("Resources response:", COLOR_GREEN)
      print_color(resources_result.to_json, COLOR_GREEN)
    rescue ex
      print_color("Error listing resources: #{ex.message}", COLOR_YELLOW)
    end
  end
  
  # Skip shutdown (method not supported by server)
  print_color("Skipping shutdown request (not supported by this server)...", COLOR_CYAN)
  
  # Exit and cleanup
  print_color("Sending exit notification and cleaning up...", COLOR_CYAN)
  client.exit
  print_color("Client exited, transport closed.", COLOR_GREEN)
  
  print_divider("=", 70, COLOR_BLUE)
  print_color("TEST CLIENT FINISHED", COLOR_BLUE, true)
  print_divider("=", 70, COLOR_BLUE)
  
rescue ex : MCPRuntimeError | MCPValueError
  print_color("MCP ERROR: #{ex.message}", COLOR_RED)
  exit(1)
rescue ex : IO::Error
  print_color("IO ERROR: #{ex.message}", COLOR_RED)
  exit(1)
rescue ex : Exception
  print_color("UNEXPECTED ERROR: #{ex.class.name} - #{ex.message}", COLOR_RED)
  ex.backtrace.each { |line| STDERR.puts "  #{line}" }
  exit(1)
end