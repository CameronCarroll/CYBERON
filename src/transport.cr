# src/transport.cr
require "json"
require "log"
require "./errors" # Assuming errors.cr is in the same directory or adjust path

# A module defining the Transport interface for MCP communications
module CyberonMCP
  module Transport
    abstract def send_and_receive(message : String) : String
  end

  # An implementation of Transport using standard input/output
  class StdioTransport
    include Transport

  # Logger for transport specific messages if needed, otherwise could use MCPClient's logger
  # @@logger = Logger.new(STDERR)
  # @@logger.level = Logger::INFO

  def initialize
    STDOUT.sync = true # Ensure immediate flushing
  end

  def send_and_receive(message : String) : String
    begin
      # @@logger.debug "Sending via stdout: #{message}"
      puts message

      response = gets
      # @@logger.debug "Received via stdin: #{response}"

      if response.nil?
        # @@logger.error "Stdin closed unexpectedly."
        raise IO::Error.new("End of stream reached on stdin while waiting for response.")
      end

      return response.strip
    rescue ex : Exception
      # @@logger.error "StdioTransport Error: #{ex.message}"
      # Construct a JSON-RPC error response
      # Note: id is nil because we might not know the original request id if send failed
      error_response = {
        jsonrpc: "2.0",
        id:      nil,
        error:   {
          code:    -32000, # Generic transport error
          message: "Transport error: Failed to send/receive message via stdio",
          data:    ex.message,
        },
      }
      return error_response.to_json
    end
  end
end

# Add other transport implementations here (e.g., HttpTransport, TcpTransport)
end