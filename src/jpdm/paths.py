"""Where the model writes its outputs. Override the root with the JPDM_ROOT environment variable."""
import os
from pathlib import Path

ROOT = Path(os.environ.get("JPDM_ROOT", Path(__file__).resolve().parents[2]))
RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"
WORKBOOK = ROOT / "workbook" / "joint_production_displacement_model.xlsx"
FIGURES = ROOT / "paper" / "figures"
