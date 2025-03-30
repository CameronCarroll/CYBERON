# src/client_main.cr

# Adjust require paths based on your project structure
# Assuming this file is in src/ and others are relative to it
require "./mcp_client"
require "./transport"
require "./errors"
require "logger" # Already required by others, but explicit here is fine

# Set log level (optional)
MCPClient.log_level = Logger::DEBUG

# --- Example Usage ---
puts "Starting MCP Client Example..."

# 1. Create Transport
# Using StdioTransport assumes the server communicates via stdin/stdout
transport = StdioTransport.new
puts "Using StdioTransport."

# 2. Create Client
client = MCPClient.new(transport)
puts "MCPClient created."

begin
  # 3. Initialize Connection
  puts "Initializing connection with server..."
  server_info = client.initialize # Note: this is the protocol `initialize`, not the constructor
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
  $stderr.puts "\n[MCP Client Error] #{ex.message}"
  exit 1
rescue ex : IOError # Catch transport errors specifically if needed
  $stderr.puts "\n[Transport Error] #{ex.message}"
  exit 1
rescue ex : Exception
  $stderr.puts "\n[Unexpected Error] #{ex.message}"
  $stderr.puts ex.backtrace.join("\n")
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