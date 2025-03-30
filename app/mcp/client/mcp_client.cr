# src/mcp_client.cr
require "json"
require "logger"

require "./transport"
require "./errors"
require "./client/features/ontology"
require "./client/features/prompts"
require "./client/features/resources"
require "./client/features/tools"

# Main MCP Client class for communicating with a CYBERON MCP server.
class MCPClient
  # The transport mechanism used for communication.
  getter transport : Transport?

  # Information about this client, sent during initialization.
  getter client_info : Hash(String, String)

  # Capabilities reported by the server after successful initialization.
  getter server_capabilities : Hash(String, JSON::Any)

  # Indicates if the client has successfully initialized with the server.
  getter initialized : Bool

  # Logger instance for logging client activities.
  @@logger = Logger.new(STDERR)

  # Sets the global log level for all MCPClient instances.
  def self.log_level=(level : Logger::Severity)
    @@logger.level = level
  end

  # --- Include Feature Modules ---
  # This adds the methods from the feature files to this class
  include Features::Ontology
  include Features::Prompts
  include Features::Resources
  include Features::Tools
  # --- End Include Feature Modules ---


  # Creates a new MCPClient instance.
  def initialize(@transport : Transport? = nil, client_name : String = "Crystal MCP Client", client_version : String = "0.1.0")
    @next_id = 1
    @initialized = false
    @server_capabilities = {} of String => JSON::Any
    @client_info = {
      "name"    => client_name,
      "version" => client_version,
    }
    @@logger.info("MCP client created. Transport #{transport ? "set" : "not set"}.")
  end

  # Sets the transport for the client
  def set_transport(transport : Transport)
    @transport = transport
    @@logger.info("Transport set to: #{transport.class.name}")
  end

  # Initializes the connection with the MCP server
  def initialize : Hash(String, JSON::Any)
    unless @transport
      raise MCPRuntimeError.new("No transport set for the client. Call set_transport first.")
    end
    if @initialized
      @@logger.warn("Client already initialized. Re-initializing.")
      @initialized = false
    end

    params = {"clientInfo" => @client_info}
    response = send_request("initialize", params)

    if error = response["error"]?
      err_obj = error.as_h? || {"code" => -32603, "message" => "Invalid error format"}
      raise MCPValueError.new("Error initializing MCP connection: #{err_obj["message"]} (Code: #{err_obj["code"]})")
    end

    result = response["result"].as_h?
    unless result
      raise MCPValueError.new("Invalid initialization response: 'result' field is missing or not an object.")
    end

    @server_capabilities = result["capabilities"].as_h? || {} of String => JSON::Any
    @initialized = true

    @@logger.info("MCP client initialized successfully with server.")
    @@logger.debug("Server capabilities: #{@server_capabilities.to_json}")

    send_notification("initialized", {} of String => String)
    @@logger.debug("Sent 'initialized' notification.")
    result
  end

  # Gets the server capabilities (could fetch or return cached)
  def get_capabilities : Hash(String, JSON::Any)
    ensure_initialized
    # For simplicity, returning cached. Could add a fetch logic if needed.
    @server_capabilities
  end

  # Sends a shutdown request
  def shutdown : Bool
    ensure_initialized
    response = send_request("shutdown", {} of String => String)
    if error = response["error"]?
      err_obj = error.as_h
      @@logger.error("Shutdown request failed: #{err_obj["message"]} (Code: #{err_obj["code"]})")
      false
    else
      @@logger.info("Shutdown request acknowledged by server.")
      true
    end
  end

  # Sends an exit notification
  def exit
    if @transport
      send_notification("exit", {} of String => String)
      @@logger.info("Sent 'exit' notification.")
    else
      @@logger.warn("Cannot send 'exit' notification, no transport available.")
    end
    @initialized = false
  end


  # --- Private Helper Methods ---

  # Sends a request and returns the response hash
  private def send_request(method : String, params) : Hash(String, JSON::Any)
    transport = @transport.not_nil! # ensure_initialized should have caught nil transport

    request_id = @next_id
    @next_id += 1

    request = {jsonrpc: "2.0", id: request_id, method: method, params: params}
    request_json = request.to_json
    @@logger.debug { "Sending request (ID: #{request_id}): #{request_json}" }

    response_json = transport.send_and_receive(request_json)
    @@logger.debug { "Received response (ID: #{request_id}): #{response_json}" }

    begin
      response = JSON.parse(response_json)
      parsed_response = response.as_h?
      unless parsed_response
        @@logger.error("Invalid JSON response type: Expected object, got #{response.class.name}. Response: #{response_json}")
        return wrap_error(-32600, "Invalid response type: Expected JSON object")
      end
      # Optional: ID check
      response_id = parsed_response["id"]?
      if !parsed_response.has_key?("error") && response_id && response_id.raw != request_id
         @@logger.warn("Received response with mismatched ID. Expected #{request_id}, got #{response_id.raw}")
      end
      parsed_response
    rescue ex : JSON::ParseException
      @@logger.error("Failed to parse JSON response: #{ex.message}. Response: #{response_json}")
      wrap_error(-32700, "Parse error: Invalid JSON received")
    rescue ex : Exception
      @@logger.error("Error processing response: #{ex.message}")
      wrap_error(-32603, "Internal error processing response: #{ex.message}")
    end
  end

  # Sends a notification (fire-and-forget, mostly)
  private def send_notification(method : String, params)
    transport = @transport.not_nil!

    notification = {jsonrpc: "2.0", method: method, params: params}
    notification_json = notification.to_json
    @@logger.debug { "Sending notification: #{notification_json}" }

    # Handling notification send depends heavily on transport capabilities
    # StdioTransport will block waiting for a response here, which is incorrect for notifications.
    # A robust solution requires a Transport interface supporting send-only,
    # or specific handling per transport type.
    if transport.is_a?(StdioTransport)
      @@logger.warn("Attempting notification via StdioTransport; may block inappropriately.")
    end
    begin
      # Call send_and_receive but ignore the response (best we can do with current Transport)
      transport.send_and_receive(notification_json)
    rescue ex : Exception
      @@logger.error("Error trying to send notification via #{transport.class.name}: #{ex.message}")
    end
  end

  # Ensures client is initialized
  private def ensure_initialized
    raise MCPRuntimeError.new("MCP client not initialized. Call the 'initialize' method first.") unless @initialized
  end

  # Ensures server supports a feature
  private def ensure_feature(*feature_path : String)
    cap_value = @server_capabilities
    feature_path.each_with_index do |key, index|
      current_path = feature_path[0..index].join('.')
      sub_value = cap_value[key]? # Use temporary variable
      if sub_value
         cap_value = sub_value # Update cap_value for next iteration only if key exists
         if index == feature_path.size - 1
            is_supported = (cap_value.is_a?(Bool) && cap_value.as_bool) || cap_value.is_a?(Hash) || cap_value.is_a?(Array) || cap_value.raw == true # Check bool specifically
            raise MCPValueError.new("Server does not support feature: '#{current_path}' (disabled or invalid value: #{cap_value.raw})") unless is_supported
            return # Feature supported
         elsif !cap_value.is_a?(Hash)
            raise MCPValueError.new("Server capability path '#{current_path}' is not a nested object, cannot check deeper.")
         end
         # If it's a hash and not the last key, continue digging in the next loop (cap_value is already updated)
         # Re-cast just to be safe if JSON::Any structure is complex
         cap_value = cap_value.as_h? || {} of String => JSON::Any
      else
         raise MCPValueError.new("Server does not support feature: '#{current_path}' (missing)")
      end
    end
  end

  # Helper to wrap errors in JSON-RPC structure
  private def wrap_error(code : Int32, message : String, data = nil) : Hash(String, JSON::Any)
    error_obj = {"code" => code, "message" => message}
    error_obj["data"] = data unless data.nil?
    # Ensure the error object itself is valid JSON::Any for the outer hash
    {
      "jsonrpc" => "2.0",
      "id"      => nil,
      "error"   => JSON.parse(error_obj.to_json),
    }
  end
end