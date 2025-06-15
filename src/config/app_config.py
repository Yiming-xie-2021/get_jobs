print("MINIMAL SETTINGS.PY: Top of file, about to define TEST_VAR")
TEST_VAR = "hello from settings"
print("MINIMAL SETTINGS.PY: TEST_VAR defined")

# Keep os for load_settings to use os.path
import os
import yaml # Keep yaml for load_settings

# Keep Settings dataclass minimal if needed by load_settings type hint
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Settings:
    hook_url: Optional[str] = None

def _recursive_dataclass_parse(config_class, data_dict):
    print(f"Minimal settings.py: In _recursive_dataclass_parse (stub for now)")
    if not isinstance(data_dict, dict):
        return data_dict
    return config_class()

def load_settings(config_path: str = "data/config.yaml"):
    print("MINIMAL SETTINGS.PY: load_settings CALLED")
    print("MINIMAL SETTINGS.PY: Returning default Settings object")
    return Settings(hook_url="test_hook_minimal")

print("MINIMAL SETTINGS.PY: Bottom of file, load_settings defined.")
