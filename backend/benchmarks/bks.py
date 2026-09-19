"""
Best Known Solution (BKS) Manager.

Provides verified BKS values and calculates percentage gap to BKS.
"""

import json
from pathlib import Path
from typing import Any, Optional

BKS_FILE = Path(__file__).resolve().parent / "bks" / "bks.json"

def load_bks_database() -> dict[str, Any]:
    """Load the BKS database JSON file."""
    if not BKS_FILE.exists():
        return {}
    with open(BKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_bks_info(instance_name: str) -> Optional[dict[str, Any]]:
    """Retrieve BKS details for an instance name."""
    db = load_bks_database()
    return db.get(instance_name)

def get_bks_value(instance_name: str) -> Optional[float]:
    """Get the numeric BKS value for an instance."""
    info = get_bks_info(instance_name)
    if info is not None:
        return float(info["bks"])
    return None

def calculate_gap_percent(cost: float, bks: float) -> float:
    """Calculate percentage gap to BKS: ((cost - BKS) / BKS) * 100."""
    if bks <= 0:
        return 0.0
    return ((cost - bks) / bks) * 100.0
