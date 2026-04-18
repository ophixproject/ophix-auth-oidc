"""
gen_version.py
~~~~~~~~~~~~~~
Reads the version from pyproject.toml and writes it to
src/ophix_auth_oidc/_version.py.

Run after bumping the version in pyproject.toml:
    python gen_version.py
"""

import tomli
import pathlib

ROOT = pathlib.Path(__file__).parent
PYPROJECT = ROOT / "pyproject.toml"
VERSION_FILE = ROOT / "src" / "ophix_auth_oidc" / "_version.py"

with open(PYPROJECT, "rb") as f:
    data = tomli.load(f)

version = data["project"]["version"]

VERSION_FILE.write_text(f'__version__ = "{version}"\n')
print(f"Wrote {VERSION_FILE} -> {version}")
