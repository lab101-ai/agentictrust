"""
Load and cache policies from YAML configuration.
"""
import yaml
from pathlib import Path
from app.config import Config


def load_policies():
    """
    Load policies from either configs/policies.yml or data/policies.yml and return list of policy dicts.
    """
    # Check configs directory first
    config_path = Path(Config.base_dir) / 'configs' / 'policies.yml'
    # Fallback to data directory
    data_path = Path(Config.base_dir) / 'data' / 'policies.yml'
    path = config_path if config_path.exists() else (data_path if data_path.exists() else None)
    if not path:
        return []
    with open(path, 'r') as f:
        loaded = yaml.safe_load(f) or {}
    return loaded.get('policies', [])
