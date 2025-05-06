"""
Validation utilities for the AgenticTrust SDK.
"""
from typing import Any, Dict, List, Optional, Union, Callable
import uuid


def validate_uuid(value: str, param_name: str = "value") -> str:
    """
    Validate that a string is a valid UUID.
    
    Args:
        value: The string to validate
        param_name: Name of the parameter (for error messages)
        
    Returns:
        The validated UUID string
        
    Raises:
        ValueError: If the value is not a valid UUID
    """
    if not value:
        raise ValueError(f"{param_name} cannot be empty")
        
    try:
        uuid_obj = uuid.UUID(value)
        return str(uuid_obj)
    except (ValueError, AttributeError, TypeError):
        raise ValueError(f"{param_name} must be a valid UUID, got {value}")


def validate_string(value: Optional[str], param_name: str = "value", required: bool = True) -> Optional[str]:
    """
    Validate that a value is a string.
    
    Args:
        value: The value to validate
        param_name: Name of the parameter (for error messages)
        required: Whether the value is required
        
    Returns:
        The validated string or None if not required and not provided
        
    Raises:
        ValueError: If the value is invalid
    """
    if value is None:
        if required:
            raise ValueError(f"{param_name} is required")
        return None
        
    if not isinstance(value, str):
        raise ValueError(f"{param_name} must be a string, got {type(value).__name__}")
        
    return value


def validate_string_list(
    value: Optional[Union[List[str], str]],
    param_name: str = "value",
    required: bool = True,
) -> Optional[List[str]]:
    """
    Validate that a value is a list of strings or a space-separated string.
    
    Args:
        value: The value to validate (list of strings or space-separated string)
        param_name: Name of the parameter (for error messages)
        required: Whether the value is required
        
    Returns:
        The validated list of strings or None if not required and not provided
        
    Raises:
        ValueError: If the value is invalid
    """
    if value is None:
        if required:
            raise ValueError(f"{param_name} is required")
        return []
        
    if isinstance(value, str):
        # Split space-separated string
        return [s.strip() for s in value.split() if s.strip()]
        
    if not isinstance(value, list):
        raise ValueError(f"{param_name} must be a list or string, got {type(value).__name__}")
        
    # Validate each item is a string
    result = []
    for i, item in enumerate(value):
        if not isinstance(item, str):
            raise ValueError(f"Item {i} in {param_name} must be a string, got {type(item).__name__}")
        if item.strip():
            result.append(item.strip())
            
    return result


def validate_bool(value: Any, param_name: str = "value", default: bool = False) -> bool:
    """
    Validate that a value is a boolean.
    
    Args:
        value: The value to validate
        param_name: Name of the parameter (for error messages)
        default: Default value if None
        
    Returns:
        The validated boolean
        
    Raises:
        ValueError: If the value is not a boolean
    """
    if value is None:
        return default
        
    if isinstance(value, bool):
        return value
        
    if isinstance(value, str):
        if value.lower() in ("true", "1", "t", "yes", "y"):
            return True
        if value.lower() in ("false", "0", "f", "no", "n"):
            return False
            
    if isinstance(value, int):
        return bool(value)
        
    raise ValueError(f"{param_name} must be a boolean, got {type(value).__name__}")


def validate_dict(
    value: Optional[Dict[str, Any]],
    param_name: str = "value",
    required: bool = True,
) -> Dict[str, Any]:
    """
    Validate that a value is a dictionary.
    
    Args:
        value: The dictionary to validate
        param_name: Name of the parameter (for error messages)
        required: Whether the value is required
        
    Returns:
        The validated dictionary or an empty dict if not required and not provided
        
    Raises:
        ValueError: If the value is not a dictionary
    """
    if value is None:
        if required:
            raise ValueError(f"{param_name} is required")
        return {}
        
    if not isinstance(value, dict):
        raise ValueError(f"{param_name} must be a dictionary, got {type(value).__name__}")
        
    return value
