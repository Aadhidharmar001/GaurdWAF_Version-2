"""
Policy Loader and YAML Parser Module for GuardWAF.
"""

import os
import yaml
from typing import Dict, Any, Union
from guardwaf.core.models import (
    PolicyConfig,
    PolicyMetadata,
    PolicyRules,
    RateLimitRule,
    SequenceRule,
    BulkThresholdRule,
    DataScopeRule,
    ParameterBlocklistRule,
    HITLRule,
)
from guardwaf.exceptions import GuardWAFConfigurationError

def parse_policy_dict(data: Dict[str, Any]) -> PolicyConfig:
    """
    Parses a dictionary representation of a policy into a validated PolicyConfig.
    """
    try:
        metadata_raw = data.get("metadata", {})
        metadata = PolicyMetadata(
            policy_name=metadata_raw.get("policy_name", "default_policy"),
            version=str(metadata_raw.get("version", "1.0")),
            description=metadata_raw.get("description", "GuardWAF Security Policy"),
        )
        shadow_mode = data.get("shadow_mode", False)

        rules_raw = data.get("rules", {})
        
        rate_limits = [RateLimitRule(**item) for item in rules_raw.get("rate_limits", [])]
        sequences = [SequenceRule(**item) for item in rules_raw.get("sequences", [])]
        bulk_thresholds = [BulkThresholdRule(**item) for item in rules_raw.get("bulk_thresholds", [])]
        data_scope = [DataScopeRule(**item) for item in rules_raw.get("data_scope", [])]
        parameter_blocklist = [ParameterBlocklistRule(**item) for item in rules_raw.get("parameter_blocklist", [])]
        hitl_rules = [HITLRule(**item) for item in rules_raw.get("hitl_rules", [])]

        rules = PolicyRules(
            rate_limits=rate_limits,
            sequences=sequences,
            bulk_thresholds=bulk_thresholds,
            data_scope=data_scope,
            parameter_blocklist=parameter_blocklist,
            hitl_rules=hitl_rules,
        )

        return PolicyConfig(metadata=metadata, shadow_mode=shadow_mode, rules=rules)
    except Exception as e:
        raise GuardWAFConfigurationError(f"Failed to parse policy configuration: {str(e)}") from e

def load_policy_from_yaml(filepath_or_content: str) -> PolicyConfig:
    """
    Loads and validates policy configuration from a YAML file path or raw YAML string.
    """
    if os.path.exists(filepath_or_content):
        with open(filepath_or_content, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = filepath_or_content

    try:
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            raise GuardWAFConfigurationError("YAML content must evaluate to a dictionary.")
        return parse_policy_dict(data)
    except Exception as e:
        if isinstance(e, GuardWAFConfigurationError):
            raise e
        raise GuardWAFConfigurationError(f"Invalid YAML syntax in policy: {str(e)}") from e
