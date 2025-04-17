import json
import os
from types import MappingProxyType
from typing import Any, Mapping

def load_config() -> Mapping[str, Any]:
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Configuration file not found at {config_path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON from {config_path}: {e}") from e

CONFIG: Mapping[str, Any] = MappingProxyType(load_config())
