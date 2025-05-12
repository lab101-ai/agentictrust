"""
Scope engine for managing and validating scopes.
"""
from typing import List, Set, Dict, Any, Optional
import traceback
import yaml
from pathlib import Path

from agentictrust.core.scope.utils import validate_scope_name
from agentictrust.core.scope.operations import expand_implied_scopes
from agentictrust.db.models import Scope
# Legacy Policy model retired – OPA is now single source of truth
from agentictrust.utils.logger import logger

class ScopeEngine:
    """Core engine for handling scope validation and expansion."""
    def __init__(self):
        # Initialize engine state and load default scopes
        self._initialize_scopes()

    def _initialize_scopes(self) -> None:
        """Load default scopes from data/scopes.yml into DB."""
        # Determine the project root (parent of the 'app' directory)
        project_root = Path(__file__).resolve().parents[3]
        data_file = project_root / 'data' / 'scopes.yml'
        logger.debug(f"Looking for scopes data file at {data_file}")
        
        # If not found, try legacy path inside app/data for backward-compatibility
        if not data_file.exists():
            alt_file = Path(__file__).resolve().parents[2] / 'data' / 'scopes.yml'
            if alt_file.exists():
                data_file = alt_file
                logger.debug(f"Using fallback scopes data file at {data_file}")

        if not data_file.exists():
            logger.info(f"Scope data file not found at {data_file}, skipping initialization.")
            return

        logger.info(f"Initializing scopes from {data_file}...")
        
        # Make sure the scopes table exists
        try:
            from sqlalchemy import inspect
            from agentictrust.db import init_db, engine as _engine

            inspector = inspect(_engine)
            if not inspector.has_table('scopes'):
                logger.info("'scopes' table missing; running init_db to create tables.")
                init_db()
        except Exception as e:
            logger.warning(f"Could not verify or create 'scopes' table: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")

        # Load and process scopes from YAML
        try:
            with open(data_file) as f:
                cfg = yaml.safe_load(f) or {}
                
            for entry in cfg.get('scopes', []):
                name = entry.get('name')
                if not name:
                    logger.warning("Skipping scope with missing name in configuration")
                    continue
                    
                # Check if scope already exists using the model method
                existing_scope = Scope.query.filter_by(name=name).first()
                if existing_scope:
                    logger.info(f"Scope '{name}' already exists, skipping.")
                    continue

                logger.info(f"Adding scope '{name}' from YAML.")
                try:
                    # Let the Scope model handle the database operations
                    Scope.create(
                        name=name,
                        description=entry.get('description'),
                        category=entry.get('category', 'basic'),
                        is_default=entry.get('is_default', False),
                        is_sensitive=entry.get('is_sensitive', False),
                        requires_approval=entry.get('requires_approval', False)
                    )
                    logger.debug(f"Successfully created scope '{name}'")
                except ValueError as ex:
                    logger.error(f"Validation error creating scope '{name}': {ex}")
                    continue
                except Exception as ex:
                    logger.error(f"Error creating scope '{name}': {ex}")
                    logger.debug(f"Exception details: {traceback.format_exc()}")
                    continue
                    
            logger.info("Scope initialization complete.")
        except Exception as e:
            logger.error(f"Failed to initialize scopes from YAML: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")
            # We don't re-raise the exception to avoid preventing app startup

    # Database-backed scope operations
    def create_scope(
        self,
        name: str,
        description: Optional[str] = None,
        category: str = 'basic',
        is_default: bool = False,
        is_sensitive: bool = False,
        requires_approval: bool = False,
        is_active: bool = True
    ) -> Dict[str, Any]:
        """Create a new scope or return existing"""
        try:
            if not name:
                logger.error("Cannot create scope: name is required")
                raise ValueError("name is required")
                
            # Validate scope name format
            validate_scope_name(name)
            
            # Check if scope already exists
            existing_scope = Scope.query.filter_by(name=name).first()
            if existing_scope:
                logger.info(f"Scope with name '{name}' already exists, returning existing scope")
                return existing_scope.to_dict()
                
            # Create the scope using the model's create method
            logger.info(f"Creating new scope '{name}'")
            scope = Scope.create(
                name=name,
                description=description,
                category=category,
                is_default=is_default,
                is_sensitive=is_sensitive,
                requires_approval=requires_approval
            )
            
            # Handle is_active separately since it's not part of Scope.create()
            if not is_active and scope:
                logger.debug(f"Setting scope '{name}' as inactive")
                scope.update(is_active=is_active)
                
            logger.info(f"Successfully created scope '{name}' (ID: {scope.scope_id})")
            return scope.to_dict()
            
        except ValueError as e:
            # Re-raise validation errors for proper client handling
            logger.warning(f"Validation error creating scope '{name}': {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating scope '{name}': {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to create scope: {str(e)}") from e

    def list_scopes(self, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all scopes, optionally filtered by level"""
        try:
            # Get all scopes using the model method
            scopes = Scope.list_all()
            
            # Apply filter in memory if needed
            if level:
                logger.debug(f"Filtering scopes by category: {level}")
                scopes = [s for s in scopes if s.category == level]
                
            result = [s.to_dict() for s in scopes]
            logger.debug(f"Retrieved {len(result)} scopes" + (f" with category '{level}'" if level else ""))
            return result
        except Exception as e:
            logger.error(f"Error listing scopes: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to list scopes: {str(e)}") from e

    def get_scope(self, scope_id: str) -> Dict[str, Any]:
        """Fetch a scope by ID"""
        try:
            # Use the model method to get the scope by ID
            scope = Scope.get_by_id(scope_id)
            logger.debug(f"Retrieved scope: {scope.name} (ID: {scope.scope_id})")
            return scope.to_dict()
        except ValueError as e:
            # Re-raise ValueError from model method (e.g., scope not found)
            raise
        except Exception as e:
            logger.error(f"Error retrieving scope {scope_id}: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to retrieve scope: {str(e)}") from e

    def update_scope(self, scope_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update scope properties"""
        try:
            if not data:
                logger.warning(f"No update data provided for scope {scope_id}")
                raise ValueError("No update data provided")
                
            # Validate name if included in update data
            if 'name' in data:
                logger.debug(f"Validating updated scope name: {data['name']}")
                validate_scope_name(data['name'])
                
            # Get the scope by ID using the model method
            scope = Scope.get_by_id(scope_id)
            
            # Use the model's update method to handle the database operations
            updated_scope = scope.update(**data)
            logger.info(f"Successfully updated scope {scope_id} ({updated_scope.name})")
            return updated_scope.to_dict()
        except ValueError as e:
            # Re-raise ValueError for client handling
            raise
        except Exception as e:
            logger.error(f"Error updating scope {scope_id}: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to update scope: {str(e)}") from e

    def delete_scope(self, scope_id: str) -> None:
        """Delete a scope by ID"""
        try:
            # Use the model's method directly, which already has error handling
            Scope.delete_by_id(scope_id)
            logger.info(f"Successfully deleted scope {scope_id}")
        except ValueError as e:
            # Re-raise ValueError for client handling (e.g., scope not found)
            raise
        except Exception as e:
            logger.error(f"Error deleting scope {scope_id}: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to delete scope: {str(e)}") from e

    def expand(self, scopes: List[str]) -> Set[str]:
        """Expand scopes to include implied permissions."""
        return expand_implied_scopes(scopes)

    def registry(self) -> List[Dict[str, Any]]:
        """Return flattened metadata for all scopes."""
        items: List[Dict[str, Any]] = []
        for scope in Scope.query.all():
            parts = scope.name.split(':')
            resource = parts[0]
            action = parts[1] if len(parts) > 1 else ''
            qualifiers = parts[2:] if len(parts) > 2 else []
            items.append({
                "name": scope.name,
                "resource": resource,
                "action": action,
                "qualifiers": qualifiers,
                "description": scope.description
            })
        return items

    def is_scope_expansion_allowed(self, requested: str, implied: str, context: Dict[str, Any]) -> bool:
        """
        Check if an implied scope can be granted based on policies for a requested scope.
        """
        # Prefer OPA rule if enabled
        try:
            from agentictrust.core.policy.opa_client import opa_client
            input_data = {
                "requested": requested,
                "implied": implied,
                "context": context,
            }
            allowed = opa_client.query_bool_sync("allow_scope_expansion", input_data)
            return allowed
        except Exception as e:
            logger.warning(f"OPA scope-expansion query failed, defaulting to allow: {e}")
            # Legacy DB-backed policy engine removed.  Default to allow on
            # OPA communication failure to preserve previous behaviour.
            return True
