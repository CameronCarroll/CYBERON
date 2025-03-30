# src/client/features/ontology.cr
require "json"
require "../../errors" # Adjust path relative to mcp_client.cr location
require "../../mcp_client" # Needed for type annotations and potential constants

# Module containing ontology-related methods for MCPClient
module MCPClient::Features::Ontology
  # Searches for entities in the ontology
  def search_entities(query : String, entity_types : Array(String)? = nil, limit : Int32 = 10) : Hash(String, JSON::Any)
    ensure_initialized
    ensure_feature("cyberon", "search")

    params = Hash{
      "query" => query,
      "limit" => limit,
    }
    params["entityTypes"] = entity_types if entity_types

    response = send_request("cyberon/search", params)

    if error = response["error"]?
      err_obj = error.as_h
      @@logger.error("Error searching entities for query '#{query}': #{err_obj["message"]} (Code: #{err_obj["code"]})")
      return {"entities" => [] of JSON::Any, "error" => err_obj, "query" => query}
    end
    response["result"].as_h? || wrap_error(-32602, "Invalid result format for cyberon/search")
  end

  # Gets detailed information about an entity
  def get_entity(entity_id : String) : Hash(String, JSON::Any)
    ensure_initialized
    ensure_feature("cyberon", "entity")

    params = {"entityId" => entity_id}
    response = send_request("cyberon/entity", params)

    if error = response["error"]?
      err_obj = error.as_h
      @@logger.error("Error getting entity #{entity_id}: #{err_obj["message"]} (Code: #{err_obj["code"]})")
      return {"error" => err_obj}
    end
    response["result"].as_h? || wrap_error(-32602, "Invalid result format for cyberon/entity")
  end

  # Finds paths between entities in the ontology
  def find_paths(source_id : String, target_id : String, max_length : Int32 = 3) : Hash(String, JSON::Any)
    ensure_initialized
    ensure_feature("cyberon", "paths")

    params = Hash{
      "sourceId"  => source_id,
      "targetId"  => target_id,
      "maxLength" => max_length,
    }
    response = send_request("cyberon/paths", params)

    if error = response["error"]?
      err_obj = error.as_h
      @@logger.error("Error finding paths between #{source_id} and #{target_id}: #{err_obj["message"]} (Code: #{err_obj["code"]})")
      return {"paths" => [] of JSON::Any, "error" => err_obj}
    end
    response["result"].as_h? || wrap_error(-32602, "Invalid result format for cyberon/paths")
  end

  # Finds connected entities in the ontology
  def find_connections(entity_id : String, max_distance : Int32 = 2) : Hash(String, JSON::Any)
    ensure_initialized
    ensure_feature("cyberon", "connections")

    params = Hash{
      "entityId"    => entity_id,
      "maxDistance" => max_distance,
    }
    response = send_request("cyberon/connections", params)

    if error = response["error"]?
      err_obj = error.as_h
      @@logger.error("Error finding connections for #{entity_id}: #{err_obj["message"]} (Code: #{err_obj["code"]})")
      return {"connections" => [] of JSON::Any, "error" => err_obj}
    end
    response["result"].as_h? || wrap_error(-32602, "Invalid result format for cyberon/connections")
  end

  # Gets all entity types in the ontology
  def get_entity_types : Hash(String, JSON::Any)
    ensure_initialized
    ensure_feature("cyberon", "entityTypes")

    response = send_request("cyberon/entityTypes", {} of String => String)

    if error = response["error"]?
      err_obj = error.as_h
      @@logger.error("Error getting entity types: #{err_obj["message"]} (Code: #{err_obj["code"]})")
      return {"entityTypes" => [] of JSON::Any, "error" => err_obj}
    end
    response["result"].as_h? || wrap_error(-32602, "Invalid result format for cyberon/entityTypes")
  end

  # Gets all relationship types in the ontology
  def get_relationship_types : Hash(String, JSON::Any)
    ensure_initialized
    ensure_feature("cyberon", "relationshipTypes")

    response = send_request("cyberon/relationshipTypes", {} of String => String)

    if error = response["error"]?
      err_obj = error.as_h
      @@logger.error("Error getting relationship types: #{err_obj["message"]} (Code: #{err_obj["code"]})")
      return {"relationshipTypes" => [] of JSON::Any, "error" => err_obj}
    end
    response["result"].as_h? || wrap_error(-32602, "Invalid result format for cyberon/relationshipTypes")
  end
end