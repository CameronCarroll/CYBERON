# src/client/features/prompts.cr
require "json"
require "../../errors"
require "../../mcp_client"

module MCPClient::Features::Prompts
  # Lists available prompts
  def list_prompts : Hash(String, JSON::Any)
    ensure_initialized
    ensure_feature("prompts")

    response = send_request("prompts/list", {} of String => String)

    if error = response["error"]?
      err_obj = error.as_h
      @@logger.error("Error listing prompts: #{err_obj["message"]} (Code: #{err_obj["code"]})")
      return {"prompts" => [] of JSON::Any, "error" => err_obj}
    end
    response["result"].as_h? || wrap_error(-32602, "Invalid result format for prompts/list")
  end

  # Gets a prompt with parameters filled in
  def get_prompt(name : String, params : Hash(String, JSON::Any)) : Hash(String, JSON::Any)
    ensure_initialized
    ensure_feature("prompts", "get")

    request_params = Hash{
      "name"   => name,
      "params" => params,
    }
    response = send_request("prompts/get", request_params)

    if error = response["error"]?
      err_obj = error.as_h
      @@logger.error("Error getting prompt '#{name}': #{err_obj["message"]} (Code: #{err_obj["code"]})")
      return {"error" => err_obj}
    end
    response["result"].as_h? || wrap_error(-32602, "Invalid result format for prompts/get")
  end
end