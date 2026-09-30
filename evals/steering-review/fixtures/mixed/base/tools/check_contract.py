"""Read-only syntax check for the synthetic source contract."""
import argparse
import ast
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--scope", choices=["source"], required=True)
parser.parse_args()
ast.parse((Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8"))
print("Source syntax valid.")
