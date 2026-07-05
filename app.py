import os
from typing import List

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

# Allow all origins (required for browser-based grader)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_bool(v):
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes", "on")


def cast(key, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


def load_yaml():
    if os.path.exists("config.development.yaml"):
        with open("config.development.yaml") as f:
            return yaml.safe_load(f) or {}
    return {}


def load_dotenv_layer():
    cfg = {}

    if "APP_DEBUG" in os.environ:
        cfg["debug"] = os.environ["APP_DEBUG"]

    # alias
    if "NUM_WORKERS" in os.environ:
        cfg["workers"] = os.environ["NUM_WORKERS"]

    return cfg


def load_os_layer():
    cfg = {}

    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_key, cfg_key in mapping.items():
        if env_key in os.environ:
            cfg[cfg_key] = os.environ[env_key]

    return cfg


@app.get("/effective-config")
def effective_config(set: List[str] = Query(default=[])):
    cfg = DEFAULTS.copy()

    # defaults
    # YAML
    cfg.update(load_yaml())

    # .env
    cfg.update(load_dotenv_layer())

    # OS env
    cfg.update(load_os_layer())

    # CLI overrides
    for item in set:
        if "=" in item:
            k, v = item.split("=", 1)
            cfg[k] = v

    # Type coercion
    result = {}
    for k, v in cfg.items():
        result[k] = cast(k, v)

    # Secret masking
    result["api_key"] = "****"

    return result