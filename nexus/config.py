import os
import json
from typing import Any, Dict

# Same support directory as the deletion audit log, so all of Nexus's
# per-user state lives in one predictable place.
CONFIG_PATH = os.path.join(
    os.path.expanduser("~"), "Library", "Application Support", "Nexus", "config.json"
)

DEFAULT_CONFIG: Dict[str, Any] = {
    "dev_cleaner": {
        "scan_dirs": ["~/Desktop", "~/Documents", "~/Developer", "~/Projects"],
        "artifact_threshold_mb": 5,
        "cache_threshold_mb": 1,
    },
    "ai_radar": {
        "cache_threshold_mb": 1,
        "loose_model_scan_dirs": ["~/Downloads", "~/Desktop"],
        "loose_model_threshold_mb": 50,
    },
    "system_cleaner": {
        "cache_threshold_mb": 1,
        "installer_threshold_mb": 5,
    },
    "app_uninstaller": {
        "orphan_threshold_mb": 2,
    },
}

_cached_config: Dict[str, Any] = None


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(force_reload: bool = False) -> Dict[str, Any]:
    """Load user config, merged over the defaults. A malformed or unreadable
    config file is ignored (falls back to defaults) rather than crashing the
    app — a typo in a hand-edited JSON file shouldn't break cleanup."""
    global _cached_config
    if _cached_config is not None and not force_reload:
        return _cached_config

    config = DEFAULT_CONFIG
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            if isinstance(user_config, dict):
                config = _deep_merge(DEFAULT_CONFIG, user_config)
        except (OSError, json.JSONDecodeError):
            pass

    _cached_config = config
    return config


def get(dotted_path: str, default: Any = None) -> Any:
    """Dotted-path getter, e.g. get('dev_cleaner.artifact_threshold_mb')."""
    node = load_config()
    for part in dotted_path.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def expand_paths(paths) -> list:
    return [os.path.expanduser(p) for p in paths]


def write_default_config_if_missing() -> bool:
    """Create config.json with the defaults on first run, so there's
    something on disk for the user to find and edit. Never overwrites an
    existing file. Returns True if it was created."""
    if os.path.exists(CONFIG_PATH):
        return False
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
            f.write("\n")
        return True
    except OSError:
        return False
