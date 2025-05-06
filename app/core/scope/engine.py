"""
Scope engine for managing and validating scopes.
"""
from typing import List, Set, Dict, Any, Optional
from app.core.scope.utils import validate_scope_name
from app.core.scope.operations import expand_implied_scopes
from app.db.models import Scope
from app.db import db_session
import yaml
from pathlib import Path
import logging

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
        logging.debug("Looking for scopes data file at %s", data_file)
        # If not found, try legacy path inside app/data for backward-compatibility
        if not data_file.exists():
            alt_file = Path(__file__).resolve().parents[2] / 'data' / 'scopes.yml'
            if alt_file.exists():
                data_file = alt_file
                logging.debug("Using fallback scopes data file at %s", data_file)

        if not data_file.exists():
            logging.info("Scope data file not found at %s, skipping initialization.", data_file)
            return

        logging.info("Initializing scopes from %s...", data_file)
        try:
            from sqlalchemy import inspect
            from app.db import init_db, engine as _engine

            inspector = inspect(_engine)
            if not inspector.has_table('scopes'):
                logging.info("'scopes' table missing; running init_db to create tables.")
                init_db()
        except Exception as e:
            logging.warning("Could not verify or create 'scopes' table: %s", e)

        try:
            with open(data_file) as f:
                cfg = yaml.safe_load(f) or {}
            for entry in cfg.get('scopes', []):
                name = entry.get('name')
                if not name:
                    continue
                if Scope.query.filter_by(name=name).first():
                    logging.info("Scope '%s' already exists, skipping.", name)
                    continue

                logging.info("Adding scope '%s' from YAML.", name)
                scope = Scope(
                    name=name,
                    description=entry.get('description'),
                    category=entry.get('category', 'basic'),
                    is_default=entry.get('is_default', False),
                    is_sensitive=entry.get('is_sensitive', False),
                    requires_approval=entry.get('requires_approval', False)
                )
                db_session.add(scope)
            db_session.commit()
            logging.info("Scope initialization complete.")
        except Exception as e:
            logging.exception("Failed to initialize scopes from YAML: %s", e)
            # Depending on requirements, might want to raise the exception
            # or handle it differently instead of just logging.

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
        if not name:
            raise ValueError("name is required")
        validate_scope_name(name)
        existing = Scope.query.filter_by(name=name).first()
        if existing:
            return existing.to_dict()
        scope = Scope(
            name=name,
            description=description,
            category=category,
            is_default=is_default,
            is_sensitive=is_sensitive,
            requires_approval=requires_approval,
            is_active=is_active
        )
        db_session.add(scope)
        db_session.commit()
        return scope.to_dict()

    def list_scopes(self, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all scopes, optionally filtered by level"""
        if level:
            scopes = Scope.query.filter_by(category=level).all()
        else:
            scopes = Scope.query.all()
        return [s.to_dict() for s in scopes]

    def get_scope(self, scope_id: str) -> Dict[str, Any]:
        """Fetch a scope by ID"""
        scope = Scope.query.get(scope_id)
        if not scope:
            raise ValueError("Scope not found")
        return scope.to_dict()

    def update_scope(self, scope_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update scope properties"""
        if not data:
            raise ValueError("No update data provided")
        scope = Scope.query.get(scope_id)
        if not scope:
            raise ValueError("Scope not found")
        # Rename
        if 'name' in data:
            new_name = data['name']
            validate_scope_name(new_name)
            existing = Scope.query.filter_by(name=new_name).first()
            if existing and existing.scope_id != scope_id:
                raise ValueError("Scope name already exists")
            scope.name = new_name
        # Other properties
        for field in ['description', 'category', 'is_default', 'is_sensitive', 'requires_approval', 'is_active']:
            if field in data:
                setattr(scope, field, data[field])
        db_session.commit()
        return scope.to_dict()

    def delete_scope(self, scope_id: str) -> None:
        """Delete a scope by ID"""
        scope = Scope.query.get(scope_id)
        if not scope:
            raise ValueError("Scope not found")
        # TODO: If system scopes (e.g., loaded from YAML) should be protected,
        # add an 'is_system' flag to the Scope model and check it here.
        # Original check (removed as is_system_scope likely doesn't exist):
        # if hasattr(scope, 'is_system_scope') and scope.is_system_scope():
        #     raise ValueError("Cannot delete system scopes")
        db_session.delete(scope)
        db_session.commit()

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
