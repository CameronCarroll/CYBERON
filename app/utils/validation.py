from typing import Dict, Any, Tuple, Optional
from flask import jsonify

def validate_entity(data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, str]]]:
    """
    Validate entity data
    
    Args:
        data: Dictionary with entity data
        
    Returns:
        Tuple of (is_valid, errors_dict)
        errors_dict is None if validation passes, otherwise contains field -> error message mapping
    """
    errors = {}
    
    if not data:
        errors["request"] = "Request body cannot be empty"
        return False, errors
    
    # Check required fields
    if 'label' not in data:
        errors["label"] = "Entity label is required"
    
    if 'type' not in data:
        errors["type"] = "Entity type is required"
    
    # Validate field types
    if 'label' in data and (not isinstance(data['label'], str) or not data['label'].strip()):
        errors["label"] = "Must be a non-empty string"
    
    if 'type' in data and (not isinstance(data['type'], str) or not data['type'].strip()):
        errors["type"] = "Must be a non-empty string. Valid types: concept, person, domain, category, technology"
    
    # Validate optional fields if present
    if 'description' in data and not isinstance(data['description'], str):
        errors["description"] = "Must be a string"
    
    if 'external_url' in data and not isinstance(data['external_url'], str):
        errors["external_url"] = "Must be a valid URL string"
    
    if 'attributes' in data:
        if not isinstance(data['attributes'], dict):
            errors["attributes"] = "Must be an object (dictionary)"
        else:
            # Validate attribute values are simple types
            invalid_attrs = []
            for key, value in data['attributes'].items():
                if not isinstance(value, (str, int, float, bool, type(None))):
                    invalid_attrs.append(key)
            
            if invalid_attrs:
                errors["attributes"] = f"The following attribute values must be simple types (string, number, boolean): {', '.join(invalid_attrs)}"
    
    return len(errors) == 0, errors if errors else None

def validate_entity_update(data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, str]]]:
    """
    Validate entity update data (less strict than create validation)
    
    Args:
        data: Dictionary with entity update data
        
    Returns:
        Tuple of (is_valid, errors_dict)
        errors_dict is None if validation passes, otherwise contains field -> error message mapping
    """
    errors = {}
    
    if not data:
        errors["request"] = "Request body cannot be empty"
        return False, errors
    
    # For updates, no fields are strictly required
    # but we validate the types of provided fields
    
    if 'label' in data and (not isinstance(data['label'], str) or not data['label'].strip()):
        errors["label"] = "Must be a non-empty string"
    
    if 'type' in data and (not isinstance(data['type'], str) or not data['type'].strip()):
        errors["type"] = "Must be a non-empty string. Valid types: concept, person, domain, category, technology"
    
    if 'description' in data and not isinstance(data['description'], str):
        errors["description"] = "Must be a string"
    
    if 'external_url' in data and not isinstance(data['external_url'], str):
        errors["external_url"] = "Must be a valid URL string"
    
    if 'attributes' in data:
        if not isinstance(data['attributes'], dict):
            errors["attributes"] = "Must be an object (dictionary)"
        else:
            # Validate attribute values are simple types
            invalid_attrs = []
            for key, value in data['attributes'].items():
                if not isinstance(value, (str, int, float, bool, type(None))):
                    invalid_attrs.append(key)
            
            if invalid_attrs:
                errors["attributes"] = f"The following attribute values must be simple types (string, number, boolean): {', '.join(invalid_attrs)}"
    
    return len(errors) == 0, errors if errors else None

def validate_relationship(data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, str]]]:
    """
    Validate relationship data
    
    Args:
        data: Dictionary with relationship data
        
    Returns:
        Tuple of (is_valid, errors_dict)
        errors_dict is None if validation passes, otherwise contains field -> error message mapping
    """
    errors = {}
    
    if not data:
        errors["request"] = "Request body cannot be empty"
        return False, errors
    
    # Check required fields
    if 'source_id' not in data:
        errors["source_id"] = "Source entity ID is required"
    
    if 'target_id' not in data:
        errors["target_id"] = "Target entity ID is required"
    
    if 'relationship_type' not in data:
        errors["relationship_type"] = "Relationship type is required"
    
    # Validate field types
    if 'source_id' in data and (not isinstance(data['source_id'], str) or not data['source_id'].strip()):
        errors["source_id"] = "Must be a non-empty string"
    
    if 'target_id' in data and (not isinstance(data['target_id'], str) or not data['target_id'].strip()):
        errors["target_id"] = "Must be a non-empty string"
    
    if 'relationship_type' in data and (not isinstance(data['relationship_type'], str) or not data['relationship_type'].strip()):
        errors["relationship_type"] = "Must be a non-empty string. Valid types: related_to, contains, depends_on, part_of, evolved_into, implemented_by"
    
    # Prevent self-relationships
    if 'source_id' in data and 'target_id' in data and data['source_id'] == data['target_id']:
        errors["target_id"] = "Source and target entities cannot be the same"
    
    # Validate optional fields if present
    if 'attributes' in data:
        if not isinstance(data['attributes'], dict):
            errors["attributes"] = "Must be an object (dictionary)"
        else:
            # Validate attribute values are simple types
            invalid_attrs = []
            for key, value in data['attributes'].items():
                if not isinstance(value, (str, int, float, bool, type(None))):
                    invalid_attrs.append(key)
            
            if invalid_attrs:
                errors["attributes"] = f"The following attribute values must be simple types (string, number, boolean): {', '.join(invalid_attrs)}"
    
    return len(errors) == 0, errors if errors else None

def validate_relationship_update(data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, str]]]:
    """
    Validate relationship update data
    
    Args:
        data: Dictionary with relationship update data
        
    Returns:
        Tuple of (is_valid, errors_dict)
        errors_dict is None if validation passes, otherwise contains field -> error message mapping
    """
    errors = {}
    
    if not data:
        errors["request"] = "Request body cannot be empty"
        return False, errors
    
    # For updates, no fields are strictly required
    # but we validate the types of provided fields
    
    if 'relationship_type' in data and (not isinstance(data['relationship_type'], str) or not data['relationship_type'].strip()):
        errors["relationship_type"] = "Must be a non-empty string. Valid types: related_to, contains, depends_on, part_of, evolved_into, implemented_by"
    
    if 'attributes' in data:
        if not isinstance(data['attributes'], dict):
            errors["attributes"] = "Must be an object (dictionary)"
        else:
            # Validate attribute values are simple types
            invalid_attrs = []
            for key, value in data['attributes'].items():
                if not isinstance(value, (str, int, float, bool, type(None))):
                    invalid_attrs.append(key)
            
            if invalid_attrs:
                errors["attributes"] = f"The following attribute values must be simple types (string, number, boolean): {', '.join(invalid_attrs)}"
    
    return len(errors) == 0, errors if errors else None