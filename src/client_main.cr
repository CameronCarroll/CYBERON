# src/client_main.cr

# Adjust require paths based on your project structure
# Assuming this file is in src/ and others are relative to it
require "./mcp_client"
require "./transport"
require "./errors"
require "log" # Crystal's built-in logging library

# Set log level (optional)
CyberonMCP::Client.log_level = Log::Severity::Info

# --- Example Usage ---
puts "Starting MCP Client Example..."

# 1. Create Transport
# Using StdioTransport assumes the server communicates via stdin/stdout
transport = CyberonMCP::StdioTransport.new
puts "Using StdioTransport."

# 2. Create Client
client = CyberonMCP::Client.new(transport)
puts "MCPClient created."

begin
  # 3. Initialize Connection
  puts "Initializing connection with server..."
  server_info = client.init_connection # Note: this is the protocol `initialize` method
  puts "Initialization successful."
  puts "Server Info: #{server_info.to_json}"
  puts "Server Capabilities: #{client.server_capabilities.to_json}"

  # 4. Use Client Methods (Examples)

  # Search entities
  begin
    puts "\nSearching entities for 'Test Query'..."
    search_results = client.search_entities(query: "Test Query", limit: 5)
    puts "Search Results: #{search_results.to_json}"
  rescue ex : MCPValueError # Handle feature not supported
    puts "Could not search entities: #{ex.message}"
  end

  # Get entity types (check if supported first using capabilities or try/catch)
  if client.server_capabilities.dig?("cyberon", "entityTypes")
     puts "\nGetting entity types..."
     entity_types = client.get_entity_types
     puts "Entity Types: #{entity_types.to_json}"
  else
     puts "\nServer does not advertise support for cyberon/entityTypes."
  end

  # Example: List tools (if supported)
  begin
     puts "\nListing tools..."
     tools_list = client.list_tools
     puts "Tools List: #{tools_list.to_json}"
  rescue ex : MCPValueError
     puts "Could not list tools: #{ex.message}"
  end

  # Add calls to other methods like get_entity, find_paths, etc.

rescue ex : MCPRuntimeError | MCPValueError
  STDERR.puts "\n[MCP Client Error] #{ex.message}"
  exit 1
rescue ex : IO::Error # Catch transport errors specifically if needed
  STDERR.puts "\n[Transport Error] #{ex.message}"
  exit 1
rescue ex : Exception
  STDERR.puts "\n[Unexpected Error] #{ex.message}"
  STDERR.puts ex.backtrace.join("\n")
  exit 1
ensure
  # 5. Shutdown Gracefully (if initialized)
  if client.initialized?
    puts "\nShutting down connection..."
    client.shutdown
    client.exit # Send exit notification
    puts "Shutdown and Exit signals sent."
  else
     puts "\nClient was not initialized, skipping shutdown."
  end
end

puts "\nMCP Client Example Finished."