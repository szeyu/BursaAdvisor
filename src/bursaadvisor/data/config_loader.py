"""
Loads per-sector JSON config files from data/sector_configs/<sector>.json.

Each sector rule file calls load_sector_config("banking") to get its thresholds
instead of hardcoding numbers or importing from constants.py.
"""
import json
from pathlib import Path

_CONFIG_DIR = Path(__file__).parent / "sector_configs"


def try_load_sector_config(sector_name: str) -> dict | None:
    """Returns config dict or None if no JSON exists for this sector."""
    try:
        return load_sector_config(sector_name)
    except FileNotFoundError:
        return None


def load_sector_config(sector_name: str) -> dict:
    path = _CONFIG_DIR / f"{sector_name.lower()}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No sector config found for '{sector_name}'. "
            f"Create {path} — use data/sector_configs/banking.json as a template."
        )
    return json.loads(path.read_text())
