import yaml
from pathlib import Path

CONFIG_PATH = Path("config.yaml")

def load_config():
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Configuration file not found at: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    return config

config = load_config()

# Example of accessing config values
if __name__ == '__main__':
    print(f"Docs path: {config['paths']['docs_path']}")
    print(f"Embedding model: {config['models']['embedding_model']}")
