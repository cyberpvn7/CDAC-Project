#!/usr/bin/env python3
"""
Centralized Configuration Management
Loads from config.yaml and environment variables
"""

import os
import yaml
from pathlib import Path


def load_config():
    """Load configuration from config.yaml and environment variables"""
    
    # Config is in config/ folder relative to project root
    config_file = Path(__file__).parent.parent / "config" / "config.yaml"
    project_root = Path(__file__).parent.parent
    
    # Default config
    default_config = {
        "database": {
            "path": os.getenv("SECGUYS_DB_PATH", str(project_root / "security_analysis.db"))
        },
        "scanner": {
            "results_dir": os.getenv("SECGUYS_SCAN_RESULTS", str(project_root / "output")),
            "timeout": int(os.getenv("SECGUYS_SCAN_TIMEOUT", "3600")),
            "parallel": os.getenv("SECGUYS_PARALLEL_SCANNERS", "false").lower() == "true"
        },
        "gemini": {
            "api_key": os.getenv("GEMINI_API_KEY", ""),
            "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        },
        "semantic": {
            "model": os.getenv("SEMANTIC_MODEL", "jackaduma/SecBERT"),
            "enabled": os.getenv("SEMANTIC_ENABLED", "true").lower() == "true"
        },
        "logging": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "dir": os.getenv("LOG_DIR", str(project_root / "output" / "logs"))
        }
    }
    
    # Load from YAML if exists
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                yaml_config = yaml.safe_load(f) or {}
                # Merge with environment overrides
                for key in default_config:
                    if key in yaml_config:
                        if isinstance(default_config[key], dict):
                            default_config[key].update(yaml_config[key])
                        else:
                            default_config[key] = yaml_config[key]
        except Exception as e:
            print(f"⚠️  Failed to load config.yaml: {e}. Using defaults.")
    
    # Validate critical config
    if not default_config["gemini"]["api_key"]:
        raise ValueError(
            "❌ GEMINI_API_KEY not set. Set via environment variable or config.yaml"
        )
    
    return default_config


# Load on import
CONFIG = load_config()
