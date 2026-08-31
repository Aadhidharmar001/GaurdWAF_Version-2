import os
import yaml
from fastapi import HTTPException
from app.models import PolicyConfig

def load_policy_from_yaml(filepath: str) -> PolicyConfig:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Policy file not found at path: {filepath}")
    with open(filepath, "r") as f:
        raw_data = yaml.safe_load(f)
        return PolicyConfig.model_validate(raw_data)

def parse_policy_yaml(yaml_content: str) -> PolicyConfig:
    raw_data = yaml.safe_load(yaml_content)
    return PolicyConfig.model_validate(raw_data)
