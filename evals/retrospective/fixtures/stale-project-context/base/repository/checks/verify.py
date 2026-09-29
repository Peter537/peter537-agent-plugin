from pathlib import Path
assert "SCHEMA_VERSION = 2" in Path("project.py").read_text()
print("Project source contract verified")
