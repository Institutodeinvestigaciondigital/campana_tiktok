"""Minimal paths for the deployed dashboard (data ships in the repo)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "data" / "processed"
NETWORKS = ROOT / "data" / "networks"
