# src/client/features/resources.cr
require "json"
require "../../errors"
require "../../mcp_client"

module MCPClient::Features::Resources
  # Lists available resources
  def list_resources(cursor : String? = nil) : Hash(String, JSON::Any)
    ensure_initialized
    ensure_feature("resources")

    params = {} of String => String?
    params["cursor"] = cursor if cursor

    response = send_request("resources/list", params)

    if error = response["error"]?
      err_obj = error.as_h
      @@logger.error("Error listing resources: #{err_obj["message"]} (Code: #{err_obj["code"]})")
      return {"resources" => [] of JSON::Any, "error" => err_obj}
    end
    response["result"].as_h? || wrap_error(-32602, "Invalid result format for resources/list")
  end

  # Lists resource templates
  def list_resource_templates(cursor : String? = nil) : Hash(String, JSON::Any)
    ensure_initialized
    ensure_feature("resources", "templates")

    params = {} of String => String?
    params["cursor"] = cursor if cursor

    response = send_request("resources/templates/list", params)

    if error = response["error"]?
      err_obj = error.as_h
      @@logger.error("Error listing resource templates: #{err_obj["message"]} (Code: #{err_obj["code"]})")
      return {"templates" => [] of JSON::Any, "error" => err_obj}
    end
    response["result"].as_h? || wrap_error(-32602, "Invalid result format for resources/templates/list")
  end

  # Reads a resource
  def read_resource(uri : String) : Hash(String, JSON::Any)
    ensure_initialized
    ensure_feature("resources", "read")

    params = {"uri" => uri}
    response = send_request("resources/read", params)

    if error = response["error"]?
      err_obj = error.as_h
      @@logger.error("Error reading resource #{uri}: #{err_obj["message"]} (Code: #{err_obj["code"]})")
      return {"error" => err_obj}
    end
    response["result"].as_h? || wrap_error(-32602, "Invalid result format for resources/read")
  end
end