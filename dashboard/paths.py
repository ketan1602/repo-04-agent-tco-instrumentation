"""Absolute paths, so the server works from any working directory."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"
COST_RESULTS = ROOT / "measurements" / "cost_results.json"
CASES = ROOT / "scenario" / "cases.json"
