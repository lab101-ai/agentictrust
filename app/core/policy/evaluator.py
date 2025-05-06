"""
Policy evaluation engine for ABAC policies.
Encapsulates a broad set of condition operators and logical evaluation in a single class.
"""
import re
import operator
import ipaddress
import fnmatch
import datetime
from functools import reduce
from typing import Any, Dict, List, Union
import json  # for parsing stored JSON conditions

from app.utils.logger import logger


class ConditionEvaluator:
    """Encapsulates ABAC operator definitions and evaluation logic."""

    # -----------------------------------------------------------------------
    # Operator implementations
    # -----------------------------------------------------------------------
    @staticmethod
    def _op_between(a: Any, bounds: List) -> bool:
        try:
            low, high = bounds
            return low <= a <= high
        except Exception:
            return False

    @staticmethod
    def _op_not_between(a: Any, bounds: List) -> bool:
        return not ConditionEvaluator._op_between(a, bounds)

    @staticmethod
    def _op_contains_any(a: Any, subset: List) -> bool:
        try:
            return bool(set(a) & set(subset))
        except Exception:
            return False

    @staticmethod
    def _op_contains_all(a: Any, subset: List) -> bool:
        try:
            return set(subset).issubset(set(a))
        except Exception:
            return False

    @staticmethod
    def _op_empty(a: Any, _: Any) -> bool:
        try:
            return len(a) == 0
        except Exception:
            return False

    @staticmethod
    def _op_not_empty(a: Any, _: Any) -> bool:
        try:
            return len(a) != 0
        except Exception:
            return False

    @staticmethod
    def _op_ilike(a: Any, b: Any) -> bool:
        try:
            return str(a).lower() == str(b).lower()
        except Exception:
            return False

    @staticmethod
    def _op_not_ilike(a: Any, b: Any) -> bool:
        return not ConditionEvaluator._op_ilike(a, b)

    @staticmethod
    def _op_regex_not(a: Any, b: Any) -> bool:
        try:
            return not bool(re.match(b, a))
        except Exception:
            return False

    @staticmethod
    def _op_wildcard(a: Any, pattern: str) -> bool:
        try:
            return fnmatch.fnmatch(str(a), pattern)
        except Exception:
            return False

    @staticmethod
    def _op_ip_in_cidr(a: str, cidrs: Union[str, List[str]]) -> bool:
        try:
            ip = ipaddress.ip_address(a)
            networks = cidrs if isinstance(cidrs, (list, tuple)) else [cidrs]
            return any(ip in ipaddress.ip_network(net) for net in networks)
        except Exception:
            return False

    @staticmethod
    def _op_ip_not_in_cidr(a: str, cidrs: Union[str, List[str]]) -> bool:
        return not ConditionEvaluator._op_ip_in_cidr(a, cidrs)

    @staticmethod
    def _parse_iso(dt_str: str) -> Union[datetime.datetime, None]:
        try:
            return datetime.datetime.fromisoformat(dt_str)
        except Exception:
            return None

    @staticmethod
    def _op_before(a: Any, b: Any) -> bool:
        t_a = ConditionEvaluator._parse_iso(a) if isinstance(a, str) else a
        t_b = ConditionEvaluator._parse_iso(b) if isinstance(b, str) else b
        try:
            return t_a < t_b
        except Exception:
            return False

    @staticmethod
    def _op_after(a: Any, b: Any) -> bool:
        t_a = ConditionEvaluator._parse_iso(a) if isinstance(a, str) else a
        t_b = ConditionEvaluator._parse_iso(b) if isinstance(b, str) else b
        try:
            return t_a > t_b
        except Exception:
            return False

    @staticmethod
    def _op_within(_unused: Any, window: Dict[str, str]) -> bool:
        """Check if current UTC time is within a time window (HH:MM)."""
        try:
            start_s = window.get('start')
            end_s = window.get('end')
            if not start_s or not end_s:
                return False
            now = datetime.datetime.utcnow().time()
            sh, sm = map(int, start_s.split(':'))
            eh, em = map(int, end_s.split(':'))
            start_t = datetime.time(sh, sm)
            end_t = datetime.time(eh, em)
            if start_t <= end_t:
                return start_t <= now <= end_t
            return now >= start_t or now <= end_t
        except Exception:
            return False

    # -----------------------------------------------------------------------
    # Mapping of operator name to function
    # -----------------------------------------------------------------------
    OPERATORS: Dict[str, Any] = {
        'eq': operator.eq,
        'ne': operator.ne,
        'lt': operator.lt,
        'le': operator.le,
        'gt': operator.gt,
        'ge': operator.ge,
        'in': lambda a, b: a in b,
        'contains': lambda a, b: b in a,
        'startswith': lambda a, b: isinstance(a, str) and a.startswith(b),
        'endswith': lambda a, b: isinstance(a, str) and a.endswith(b),
        'regex': lambda a, b: isinstance(a, str) and bool(re.match(b, a)),
        'between': _op_between.__func__,
        'not_between': _op_not_between.__func__,
        'one_of': lambda a, b: a in b,
        'contains_any': _op_contains_any.__func__,
        'contains_all': _op_contains_all.__func__,
        'len_eq': lambda a, b: len(a) == b,
        'len_lt': lambda a, b: len(a) < b,
        'len_gt': lambda a, b: len(a) > b,
        'empty': _op_empty.__func__,
        'not_empty': _op_not_empty.__func__,
        'ilike': _op_ilike.__func__,
        'not_ilike': _op_not_ilike.__func__,
        'regex_not': _op_regex_not.__func__,
        'wildcard': _op_wildcard.__func__,
        'ip_in_cidr': _op_ip_in_cidr.__func__,
        'ip_not_in_cidr': _op_ip_not_in_cidr.__func__,
        'before': _op_before.__func__,
        'after': _op_after.__func__,
        'within': _op_within.__func__,
    }

    @staticmethod
    def get_attribute_value(context: Dict[str, Any], path: str) -> Any:
        """Fetch a nested attribute from context by dot notation."""
        try:
            return reduce(lambda d, k: d.get(k, {}) if isinstance(d, dict) else {}, path.split('.'), context)
        except Exception:
            return None

    @classmethod
    def evaluate_condition(cls, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate one condition (leaf or logical) against context."""
        if not isinstance(condition, dict):
            logger.warning(f"Invalid condition: {condition}")
            return False
        # logical operators
        if 'and' in condition:
            return all(cls.evaluate_condition(c, context) for c in condition['and'])
        if 'or' in condition:
            return any(cls.evaluate_condition(c, context) for c in condition['or'])
        if 'not' in condition:
            return not cls.evaluate_condition(condition['not'], context)
        # leaf condition (supports value_from or value)
        has_required = all(k in condition for k in ('attribute', 'operator')) and (
            'value' in condition or 'value_from' in condition
        )
        if has_required:
            attr = condition['attribute']
            op = condition['operator']
            if 'value' in condition:
                val = condition['value']
            else:
                # Dynamically pull comparison value from context using dot notation
                val = cls.get_attribute_value(context, condition['value_from'])
            actual = cls.get_attribute_value(context, attr)
            fn = cls.OPERATORS.get(op)
            if not fn:
                logger.warning(f"Unknown operator: {op}")
                return False
            try:
                return fn(actual, val)
            except Exception as e:
                logger.warning(f"Error in eval {op}: {e}")
                return False
        logger.warning(f"Invalid condition format: {condition}")
        return False

    @classmethod
    def evaluate_conditions(cls, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Entry point: evaluate a conditions tree against context."""
        # Ensure we have a dict: parse JSON string or use dict directly
        if isinstance(conditions, str):
            try:
                cond = json.loads(conditions)
            except Exception as ex:
                logger.warning(f"Failed to parse conditions JSON: {ex}")
                return False
        elif isinstance(conditions, dict):
            cond = conditions
        else:
            logger.warning(f"Unsupported conditions type: {type(conditions)}")
            return False
        # Unwrap 'custom' wrapper if present
        if 'custom' in cond and isinstance(cond['custom'], dict):
            cond = cond['custom']
        # Evaluate the (possibly unwrapped) conditions
        return cls.evaluate_condition(cond or {}, context)


# Module-level convenience
evaluate_condition = ConditionEvaluator.evaluate_condition
evaluate_conditions = ConditionEvaluator.evaluate_conditions
