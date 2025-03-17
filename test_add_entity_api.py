#!/usr/bin/env python3
"""
Test script to add an entity to the Cybernetics Digital Garden via the API.

Usage:
    python test_add_entity.py [host] [port]

Arguments:
    host: API host (default: localhost)
    port: API port (default: 5001)
"""

import sys
import json
import requests
from datetime import datetime

def add_entity(base_url, entity_data):
    """
    Add an entity to the knowledge graph.
    
    Args:
        base_url: Base URL of the API
        entity_data: Dictionary with entity data
        
    Returns:
        Tuple of (success, response_data)
    """
    url = f"{base_url}/api/entities"
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=entity_data, headers=headers)
        response_data = response.json()
        
        if response.status_code == 201 and response_data.get("success"):
            return True, response_data
        else:
            error_msg = response_data.get("error", "Unknown error")
            return False, error_msg
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {str(e)}"
    except json.JSONDecodeError:
        return False, "Invalid JSON response"

def main():
    # Get host and port from command line args or use defaults
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = sys.argv[2] if len(sys.argv) > 2 else "5001"
    
    base_url = f"http://{host}:{port}"
    print(f"Using API at {base_url}")
    
    # Current timestamp for creating a unique entity
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    # Sample entity data
    entity_data = {
        "label": f"Test Entity {timestamp}",
        "type": "concept",
        "description": "A test entity created via the API",
        "external_url": "https://example.com/test-entity",
        "attributes": {
            "test_attribute": "test_value",
            "created_via": "API test script",
            "timestamp": timestamp
        }
    }
    
    print(f"\nAttempting to create entity: {entity_data['label']}")
    
    # Add the entity
    success, result = add_entity(base_url, entity_data)
    
    if success:
        entity = result.get("entity", {})
        entity_id = entity.get("id", "unknown")
        attributes = entity.get("attributes", {})
        
        print(f"\n✅ Entity created successfully!")
        print(f"ID: {entity_id}")
        print(f"Label: {attributes.get('label')}")
        print(f"Type: {attributes.get('type')}")
        print(f"Created at: {attributes.get('created_at')}")
        
        # Print the API URL to retrieve this entity
        print(f"\nYou can retrieve this entity at:")
        print(f"{base_url}/api/entities/{entity_id}")
    else:
        print(f"\n❌ Failed to create entity: {result}")
        sys.exit(1)

if __name__ == "__main__":
    main()