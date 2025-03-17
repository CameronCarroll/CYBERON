from typing import Optional, Dict, Any

def validate_entity(data: Dict[str, Any]) -> Optional[str]:
    """
    Validate entity data
    
    Args:
        data: Dictionary with entity data
        
    Returns:
        Error message if validation fails, None otherwise
    """
    if not data:
        return "Request body cannot be empty"
    
    # Check required fields
    if 'label' not in data:
        return "Entity label is required"
    
    if 'type' not in data:
        return "Entity type is required"
    
    # Validate field types
    if not isinstance(data['label'], str) or not data['label'].strip():
        return "Entity label must be a non-empty string"
    
    if not isinstance(data['type'], str) or not data['type'].strip():
        return "Entity type must be a non-empty string"
    
    # Validate optional fields if present
    if 'description' in data and not isinstance(data['description'], str):
        return "Entity description must be a string"
    
    if 'external_url' in data and not isinstance(data['external_url'], str):
        return "External URL must be a string"
    
    if 'attributes' in data and not isinstance(data['attributes'], dict):
        return "Attributes must be an object"
    
    return None  # No validation errors

def validate_entity_update(data: Dict[str, Any]) -> Optional[str]:
    """
    Validate entity update data (less strict than create validation)
    
    Args:
        data: Dictionary with entity update data
        
    Returns:
        Error message if validation fails, None otherwise
    """
    if not data:
        return "Request body cannot be empty"
    
    # For updates, no fields are strictly required
    # but we validate the types of provided fields
    
    if 'label' in data and (not isinstance(data['label'], str) or not data['label'].strip()):
        return "Entity label must be a non-empty string"
    
    if 'type' in data and (not isinstance(data['type'], str) or not data['type'].strip()):
        return "Entity type must be a non-empty string"
    
    if 'description' in data and not isinstance(data['description'], str):
        return "Entity description must be a string"
    
    if 'external_url' in data and not isinstance(data['external_url'], str):
        return "External URL must be a string"
    
    if 'attributes' in data and not isinstance(data['attributes'], dict):
        return "Attributes must be an object"
    
    return None  # No validation errors

def validate_relationship(data: Dict[str, Any]) -> Optional[str]:
    """
    Validate relationship data
    
    Args:
        data: Dictionary with relationship data
        
    Returns:
        Error message if validation fails, None otherwise
    """
    if not data:
        return "Request body cannot be empty"
    
    # Check required fields
    if 'source_id' not in data:
        return "Source entity ID is required"
    
    if 'target_id' not in data:
        return "Target entity ID is required"
    
    if 'relationship_type' not in data:
        return "Relationship type is required"
    
    # Validate field types
    if not isinstance(data['source_id'], str) or not data['source_id'].strip():
        return "Source entity ID must be a non-empty string"
    
    if not isinstance(data['target_id'], str) or not data['target_id'].strip():
        return "Target entity ID must be a non-empty string"
    
    if not isinstance(data['relationship_type'], str) or not data['relationship_type'].strip():
        return "Relationship type must be a non-empty string"
    
    # Prevent self-relationships
    if data['source_id'] == data['target_id']:
        return "Source and target entities cannot be the same"
    
    # Validate optional fields if present
    if 'attributes' in data and not isinstance(data['attributes'], dict):
        return "Attributes must be an object"
    
    return None  # No validation errors

def validate_relationship_update(data: Dict[str, Any]) -> Optional[str]:
    """
    Validate relationship update data
    
    Args:
        data: Dictionary with relationship update data
        
    Returns:
        Error message if validation fails, None otherwise
    """
    if not data:
        return "Request body cannot be empty"
    
    # For updates, no fields are strictly required
    # but we validate the types of provided fields
    
    if 'relationship_type' in data and (not isinstance(data['relationship_type'], str) or not data['relationship_type'].strip()):
        return "Relationship type must be a non-empty string"
    
    if 'attributes' in data and not isinstance(data['attributes'], dict):
        return "Attributes must be an object"
    
    return None  # No validation errors