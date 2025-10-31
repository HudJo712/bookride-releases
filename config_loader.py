import os
import yaml


def load_config():
    env = os.getenv("APP_ENV", "dev").lower()
    with open("config.yaml", "r", encoding="utf-8") as f:
        configs = yaml.safe_load(f)
    if env not in configs:
        raise ValueError(f"Invalid APP_ENV: {env}")
    cfg = configs[env]
    if isinstance(cfg.get("DEBUG"), str):
        cfg["DEBUG"] = cfg["DEBUG"].lower() == "true"
    return cfg


if __name__ == "__main__":
    c = load_config()
    print(f"Loaded: {os.getenv('APP_ENV', 'dev')}")
    for k, v in c.items():
        print(f"{k} = {v}")
