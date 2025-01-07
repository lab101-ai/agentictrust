from typing import Union
import json
from datetime import datetime, timezone
from functools import wraps
from importlib.metadata import version
from pprint import pformat
from uuid import UUID
import requests

from .descriptor import agentictrust_property
from .log_config import logger

def get_ISO_time():
    """
    Get the current UTC time in ISO 8601 format with milliseconds precision in UTC timezone.

    Returns:
        str: The current UTC time as a string in ISO 8601 format.
    """
    return datetime.now(timezone.utc).isoformat()

def is_jsonable(value):
    try:
        json.dumps(value)
        return True
    except (TypeError, OverflowError):
        return False
    
def filter_unjsonable(d: dict) -> dict:
    """
    Recursively filter a dictionary to ensure all values are JSON serializable.
    
    Args:
        d (dict): The input dictionary to filter
        
    Returns:
        dict: A new dictionary with all non-JSON-serializable values replaced with empty strings.
            - Dictionary values are recursively filtered
            - List values have each element recursively filtered 
            - UUID objects are converted to strings
            - JSON-serializable values are kept as-is
            - Any other values are replaced with empty strings
    """
    def _filter_recursively(obj):
        if isinstance(obj, dict):
            return {k: _filter_recursively(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_filter_recursively(item) for item in obj]
        elif isinstance(obj, UUID):
            return str(obj)
        elif is_jsonable(obj):
            return obj
        else:
            return ""

    return _filter_recursively(d)
    
def safe_serialize(obj):
    """
    Safely serialize an object to a JSON string.
    
    This function handles serialization of various object types by attempting different
    serialization methods and falling back gracefully. It removes problematic values
    and provides informative messages for non-serializable objects.
    
    Args:
        obj: The object to serialize. Can be any Python object.
        
    Returns:
        str: A JSON string representation of the object with:
            - UUID objects converted to strings
            - Objects with serialization methods (model_dump_json, to_json, json, etc) handled appropriately
            - Dictionary values converted to strings
            - List elements converted to strings
            - Non-serializable objects replaced with descriptive messages
            - None values and "self" keys removed
            - Serialization errors caught and replaced with error messages
    """
    def default(o):
        try:
            if isinstance(o, UUID):
                return str(o)
            elif hasattr(o, "model_dump_json"):
                return str(o.model_dump_json())
            elif hasattr(o, "to_json"):
                return str(o.to_json())
            elif hasattr(o, "json"):
                return str(o.json())
            elif hasattr(o, "to_dict"):
                return {k: str(v) for k, v in o.to_dict().items() if not callable(v)}
            elif hasattr(o, "dict"):
                return {k: str(v) for k, v in o.dict().items() if not callable(v)}
            elif isinstance(o, dict):
                return {k: str(v) for k, v in o.items()}
            elif isinstance(o, list):
                return [str(item) for item in o]
            else:
                return f"<<non-serializable: {type(o).__qualname__}>>"
        except Exception as e:
            return f"<<serialization-error: {str(e)}>>"

    def remove_unwanted_items(value):
        """Recursively remove self key and None/... values from dictionaries so they aren't serialized"""
        if isinstance(value, dict):
            return {
                k: remove_unwanted_items(v) for k, v in value.items() if v is not None and v is not ... and k != "self"
            }
        elif isinstance(value, list):
            return [remove_unwanted_items(item) for item in value]
        else:
            return value

    cleaned_obj = remove_unwanted_items(obj)
    return json.dumps(cleaned_obj, default=default)

def check_class_stack_for_agent_id() -> Union[UUID, None]:
    """
    Check the class stack for an agentictrust_property with the name 'agentictrust_agent_id'.
    """
    return agentictrust_property.stack_lookup()

def get_agentictrust_version():
    """
    Get the version of the agentictrust package.
    """
    try:
        pkg_version = version("agentictrust")
        return pkg_version
    except Exception as e:
        logger.warning("Error reading package version: %s", e)
        return None

def check_agentictrust_update():
    """
    Check if the installed AgenticTrust package version matches the latest version on PyPI.
    
    This function makes a request to PyPI to get the latest published version and compares
    it with the locally installed version. If they don't match, it logs a warning message.

    Returns:
        bool: True if check was successful, False if there was an error
    """
    try:
        response = requests.get("https://pypi.org/pypi/agentictrust/json")
        if response.status_code == 200:
            json_data = response.json()
            latest_version = json_data["info"]["version"]
            current_version = get_agentictrust_version()
            if latest_version != current_version:
                logger.warning(
                    f"AgenticTrust is out of date. Current version: {current_version}, "
                    f"Latest version: {latest_version}. Please update to the latest version."
                )
            return True
    except Exception as e:
        logger.warning("Error checking for AgenticTrust update: %s", e)
        return False
    

def debug_print_function_params(func):
    """
    Decorator to print function parameters to the log.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        logger.debug("<AGENTICTRUST>")
        logger.debug(f"Function: {func.__name__}")
        for key, value in kwargs.items():
            logger.debug(f"{key}: {pformat(value)}")

        logger.debug("</AGENTOPS_DEBUG_OUTPUT>\n")

        return func(self, *args, **kwargs)

    return wrapper
