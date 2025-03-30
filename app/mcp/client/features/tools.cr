# src/client/features/tools.cr
require "json"
require "../../errors"
require "../../mcp_client"

module MCPClient::Features::Tools
  # Lists available tools
  def list_tools : Hash(String, JSON::Any)
    ensure_initialized
    ensure_feature("tools")

    response = send_request("tools/list", {} of String => String)

    if error = response["error"]?
      err_obj = error.as_h
      @@logger.error("Error listing tools: #{err_obj["message"]} (Code: #{err_obj["code"]})")
      return {"tools" => [] of JSON::Any, "error" => err_obj}
    end
    response["result"].as_h? || wrap_error(-32602, "Invalid result format for tools/list")
  end

  # Gets the schema for a tool
  def get_tool_schema(name : String) : Hash(String, JSON::Any)
    ensure_initialized
    ensure_feature("tools", "schema")

    params = {"name" => name}
    response = send_request("tools/schema", params)

    if error = response["error"]?
      err_obj = error.as_h
      @@logger.error("Error getting tool schema for '#{name}': #{err_obj["message"]} (Code: #{err_obj["code"]})")
      return {"error" => err_obj}
    end
    response["result"].as_h? || wrap_error(-32602, "Invalid result format for tools/schema")
  end

  # Executes a tool
  def execute_tool(name : String, params : Hash(String, JSON::Any)) : Hash(String, JSON::Any)
    ensure_initialized
    ensure_feature("tools", "execute")

    request_params = Hash{
      "name"   => name,
      "params" => params,
    }
    response = send_request("tools/execute", request_params)

    if error = response["error"]?
      err_obj = error.as_h
      @@logger.error("Error executing tool '#{name}': #{err_obj["message"]} (Code: #{err_obj["code"]})")
      return {"error" => err_obj}
    end
    response["result"].as_h? || wrap_error(-32602, "Invalid result format for tools/execute")
  end
end