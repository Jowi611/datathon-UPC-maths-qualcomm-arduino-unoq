import os
from pathlib import Path

# Root directory of the repository (parent of the 'copilot' package)
ROOT = Path(__file__).resolve().parent.parent

def load_config():
    # Default fallback configuration values
    config = {
        "LLM_PORT": "8081",
        "EMBED_PORT": "8082",
        "VISION_PORT": "8083",
        "SEED": "42"
    }

    # Read from root config.env if it exists
    env_path = ROOT / "config.env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip().strip('"\'')

    # Allow environment variables to override
    for key in config:
        if key in os.environ:
            config[key] = os.environ[key]

    return config

CONFIG = load_config()