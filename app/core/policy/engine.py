"""
Policy engine for managing and enforcing policy rules.
"""
from typing import Any, Dict, List, Optional
import json
import traceback

from app.db.models import Policy, Scope
from app.core.policy.evaluator import evaluate_conditions
from app.core.policy.loader import load_policies
from app.utils.logger import logger


class PolicyEngine:
    """Core engine for loading and evaluating policies."""
    def __init__(self):
        # Initialize engine state and load default policies
        self._initialize_policies()
        
    def _initialize_policies(self) -> None:
        """Load default policies from data/policies.yml into DB."""
        # Load policies from YAML via loader
        policy_configs = load_policies()
        if not policy_configs:
            logger.info("No policies found in data/policies.yml, skipping initialization.")
            return
            
        logger.info("Initializing policies from data/policies.yml...")
        try:
            # Use Policy.create() for proper JSON encoding and scope relationships
            for entry in policy_configs:
                name = entry.get('name')
                if not name:
                    logger.warning("Skipping policy with missing name in configuration")
                    continue
                    
                # Check if policy already exists using the model method
                existing_policy = Policy.find_by_name(name)
                if existing_policy:
                    logger.info(f"Policy '{name}' already exists, skipping.")
                    continue

                # Resolve scopes by name to IDs
                raw_scopes = entry.get('scopes') or []
                scope_ids = []
                missing_scopes = []
                
                # Resolve scope objects to IDs
                if raw_scopes:
                    for scope_name in raw_scopes:
                        scope = Scope.query.filter_by(name=scope_name).first()
                        if scope:
                            scope_ids.append(scope.scope_id)
                        else:
                            missing_scopes.append(scope_name)
                    
                    if missing_scopes:
                        logger.warning(f"Missing scopes for policy '{name}': {', '.join(missing_scopes)}")

                # Wrap conditions dict under 'custom'
                raw_cond = entry.get('conditions') or {}
                cond_obj = {'custom': raw_cond} if isinstance(raw_cond, dict) else {}

                logger.info(f"Creating policy '{name}' via Policy.create()")
                try:
                    Policy.create(
                        name=name,
                        description=entry.get('description', ''),
                        conditions=cond_obj,
                        effect=entry.get('effect', 'allow'),
                        priority=entry.get('priority', 10),
                        scope_ids=scope_ids,
                    )
                    logger.debug(f"Successfully created policy '{name}'")
                except ValueError as ex:
                    logger.error(f"Validation error creating policy '{name}': {ex}")
                    continue
                except Exception as ex:
                    logger.error(f"Error creating policy '{name}': {ex}")
                    logger.debug(f"Exception details: {traceback.format_exc()}")
                    continue
                    
            logger.info("Policy initialization complete.")
        except Exception as e:
            logger.error(f"Failed to initialize policies from YAML: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")
            # We don't re-raise the exception to avoid preventing app startup

    def is_scope_expansion_allowed(
        self,
        requested: str,
        implied: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Check if an implied scope can be granted based on policies for a requested scope.
        """
        # Find policies that apply to requested scope
        policies = Policy.query.all()
        for policy in policies:
            # Check if policy applies to the requested scope
            if any(s.name == requested for s in policy.scopes):
                # If policy contains conditions to evaluate
                if policy.conditions:
                    if evaluate_conditions(policy.conditions, context):
                        # Policy matches, check if it allows expansion
                        return True
        
        # By default allow expansion if no policies restrict it
        return True

    def evaluate_policies(self, context: Dict[str, Any]) -> List[str]:
        """
        Evaluate all policies against the provided context.
        Returns list of policy names that match.
        """
        allowed = []
        for policy in Policy.query.all():
            cond = policy.conditions
            if evaluate_conditions(cond, context):
                allowed.append(policy.name)
        return allowed

    def create_policy(
        self,
        name: str,
        description: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        effect: str = 'allow',
        priority: int = 10,
        conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new policy in the database."""
        if not name:
            raise ValueError("Policy name is required")
        if Policy.query.filter_by(name=name).first():
            raise ValueError("Policy with this name already exists")
        cond: Dict[str, Any] = {}
        scope_ids: List[str] = []
        
        if scopes is not None:
            missing_scopes: List[str] = []

            for scope_name in scopes:
                # If already a UUID, keep as is
                if isinstance(scope_name, str) and len(scope_name) == 36 and "-" in scope_name:
                    scope_ids.append(scope_name)
                    continue

                scope_obj = Scope.query.filter_by(name=scope_name).first()
                if scope_obj:
                    scope_ids.append(scope_obj.scope_id)
                    logging.debug(f"Resolved scope '{scope_name}' to ID {scope_obj.scope_id}")
                else:
                    missing_scopes.append(scope_name)

            if missing_scopes:
                raise ValueError(
                    f"The following scopes are not defined: {', '.join(missing_scopes)}. "
                    "Please create these scopes first."
                )

        if conditions is not None:
            cond['custom'] = conditions
            
        # Create policy (Policy.create will JSON-encode dict conditions)
        policy = Policy.create(
            name=name,
            conditions=cond,
            effect=effect,
            description=description,
            priority=priority,
            scope_ids=scope_ids  # Pass scope IDs directly for relationship creation
        )
        return policy.to_dict()

    def list_policies(self) -> List[Dict[str, Any]]:
        """List all policies."""
        try:
            # Use the model's list_all method instead of direct query
            policies = Policy.list_all()
            return [p.to_dict() for p in policies]
        except Exception as e:
            logger.error(f"Error listing policies: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to list policies: {str(e)}") from e

    def get_policy(self, policy_id: str) -> Dict[str, Any]:
        """Get policy by ID."""
        try:
            # Use the model's get_by_id method instead of direct query
            policy = Policy.get_by_id(policy_id)
            policy_dict = policy.to_dict()
            
            # Handle transition for policies that have scopes in conditions but not in relationship
            if not policy_dict['scopes'] and 'conditions' in policy_dict:
                conditions = policy_dict['conditions']
                
                if isinstance(conditions, dict) and 'scopes' in conditions and conditions['scopes']:
                    logger.info(f"Policy {policy_id} has scopes in conditions but not in relationship")
                    scope_names = conditions['scopes']
                    scope_ids = []
                    
                    for scope_name in scope_names:
                        scope = Scope.query.filter_by(name=scope_name).first()
                        if scope:
                            scope_ids.append(scope.scope_id)
                    
                    if scope_ids:
                        new_conditions = {k: v for k, v in conditions.items() if k != 'scopes'}
                        policy.update(scope_ids=scope_ids, conditions=new_conditions)
                        policy_dict['scopes'] = scope_ids
                        policy_dict['conditions'] = new_conditions
            return policy_dict
        except ValueError as e:
            # Re-raise ValueError from the model's get_by_id method
            raise
        except Exception as e:
            logger.error(f"Error retrieving policy {policy_id}: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to update policy: {str(e)}") from e

    def update_policy(self, policy_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing policy."""
        try:
            if not data:
                logger.warning(f"No update data provided for policy {policy_id}")
                raise ValueError("No update data provided")
                
            # Get policy using the model method
            policy = Policy.get_by_id(policy_id)
            
            # Process conditions if provided
            if 'conditions' in data and isinstance(data['conditions'], dict):
                cond_obj = data['conditions']
                
                # Handle migration of scopes from conditions to relationship
                if 'scopes' in cond_obj and isinstance(cond_obj['scopes'], list):
                    logger.info(f"Migrating scopes from conditions to relationship for policy {policy_id}")
                    scope_ids: List[str] = []
                    missing_scopes: List[str] = []
                    
                    for scope_name in cond_obj['scopes']:
                        # If already a UUID, keep as is
                        if isinstance(scope_name, str) and len(scope_name) == 36 and "-" in scope_name:
                            scope_ids.append(scope_name)
                            continue

                        # Otherwise look up by name
                        scope_obj = Scope.query.filter_by(name=scope_name).first()
                        if scope_obj:
                            scope_ids.append(scope_obj.scope_id)
                            logger.debug(f"Resolved scope '{scope_name}' to ID {scope_obj.scope_id}")
                        else:
                            missing_scopes.append(scope_name)
                    
                    if missing_scopes:
                        err_msg = f"The following scopes are not defined: {', '.join(missing_scopes)}. Please create these scopes first."
                        logger.error(f"Policy update error: {err_msg}")
                        raise ValueError(err_msg)

                    # Move scopes from conditions to relationship
                    if scope_ids:
                        data['scope_ids'] = scope_ids
                        
                        # Remove scopes key from conditions since it's now in relationship
                        new_conditions = {k: v for k, v in cond_obj.items() if k != 'scopes'}
                        data['conditions'] = new_conditions
                        logger.info(f"Migrated {len(scope_ids)} scopes from conditions to relationship for policy {policy_id}")
                        
                # Make sure to properly encode/handle the conditions
                # For custom conditions, wrap in 'custom' key
                if 'custom' not in cond_obj and ('client_id' in cond_obj or 'scopes' in cond_obj):
                    data['conditions'] = {'custom': cond_obj}
                else:
                    data['conditions'] = cond_obj

            # Update the policy using the model's update method
            updated_policy = policy.update(**data)
            logger.info(f"Successfully updated policy {policy_id}")
            return updated_policy.to_dict()
            
        except ValueError as e:
            # Re-raise ValueError for client handling
            raise
        except Exception as e:
            logger.error(f"Error updating policy {policy_id}: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to update policy: {str(e)}") from e
            
    def delete_policy(self, policy_id: str) -> None:
        """Delete a policy by ID."""
        try:
            Policy.delete_by_id(policy_id)
            logger.info(f"Successfully deleted policy {policy_id}")
        except ValueError as e:
            # Re-raise ValueError for client handling (e.g., policy not found)
            raise
        except Exception as e:
            logger.error(f"Error deleting policy {policy_id}: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to delete policy: {str(e)}") from e

    def requires_human_approval(self, client_id: str, scopes: List[str], response_type: str) -> bool:
        """
        Determine if the authorization flow requires human consent based on policy rules.
        """
        # Build a context for policy evaluation
        context = {
            'client_id': client_id,
            'scopes': scopes,
            'response_type': response_type
        }
        # Check for policies that explicitly require consent
        for policy in Policy.query.filter_by(effect='consent_required').all():
            if policy.conditions and evaluate_conditions(policy.conditions, context):
                return True
        return False

    # ------------------------------------------------------------------
    # Deterministic evaluation with priority / conflict resolution
    # ------------------------------------------------------------------

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return a structured decision applying priority & deny-overrides.

        The decision object contains:
            allowed: bool – final permit/deny result
            decision: "allow" | "deny" | "none"
            matched: [policy_id, ...] – ordered list of matched policies
            denied_by: policy_id | None – first deny policy that triggered
        """
        try:
            # Fetch and sort policies by ascending priority (lower = higher precedence)
            # Use the model's list_all method instead of direct query
            policies = Policy.list_all()
            policies = sorted(policies, key=lambda p: p.priority)

            matched: List[str] = []
            denied_by: Optional[str] = None

            for pol in policies:
                try:
                    if not pol.conditions:
                        # no conditions means unconditional
                        match = True
                    else:
                        match = evaluate_conditions(pol.conditions, context)
                except Exception as eval_error:
                    logger.error(f"Error evaluating policy '{pol.name}': {eval_error}")
                    logger.debug(f"Exception details: {traceback.format_exc()}")
                    # Skip this policy on error
                    match = False

                if match:
                    matched.append(pol.policy_id)
                    logger.debug(f"Policy matched: {pol.name} (ID: {pol.policy_id}, effect: {pol.effect})")
                    if pol.effect.lower() == "deny":
                        denied_by = pol.policy_id
                        logger.info(f"Access denied by policy: {pol.name} (ID: {pol.policy_id})")
                        # deny overrides any allow even at same priority level
                        break

            allowed = denied_by is None and bool(matched)
            decision = "deny" if denied_by else ("allow" if matched else "none")
            
            result = {
                "allowed": allowed,
                "decision": decision,
                "matched": matched,
                "denied_by": denied_by,
            }
            
            logger.debug(f"Policy evaluation result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during policy evaluation: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")
            # Return a safe default in case of errors
            return {
                "allowed": False,
                "decision": "error",
                "matched": [],
                "denied_by": None,
                "error": str(e)
            }
