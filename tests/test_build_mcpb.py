"""The Claude Desktop Extension (M5-slim; `scripts/build_mcpb.py`).

The manifest follows the MCPB v0.4 schema's required fields and types, carries
the wheel it launches, and names no key or secret anywhere.
"""

from __future__ import annotations

import importlib.util
import json
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("build_mcpb", ROOT / "scripts" / "build_mcpb.py")
build_mcpb = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(build_mcpb)


#: The project's version, read the way the release workflow reads it (M6-beta).
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
WHEEL = f"nexus_scholar-{VERSION}-py3-none-any.whl"


def _bundle(tmp_path: Path) -> zipfile.ZipFile:
    wheel = tmp_path / WHEEL
    wheel.write_bytes(b"PK\x05\x06" + b"\x00" * 18)  # an empty zip stands in for the wheel
    return zipfile.ZipFile(build_mcpb.build(wheel, tmp_path / "dist"))


def test_the_manifest_meets_the_v04_schema_shape(tmp_path):
    bundle = _bundle(tmp_path)
    manifest = json.loads(bundle.read("manifest.json"))
    # Required by mcpb-manifest-v0.4.schema.json.
    for field in ("name", "version", "description", "author", "server"):
        assert field in manifest, field
    assert manifest["manifest_version"] == "0.4"
    assert manifest["author"]["name"]
    server = manifest["server"]
    assert server["type"] in ("python", "node", "binary", "uv")
    assert {"type", "entry_point", "mcp_config"} <= set(server)
    assert server["entry_point"] in bundle.namelist()
    assert server["mcp_config"]["command"] == "uvx"
    assert set(manifest["compatibility"]["runtimes"]) <= {"python", "node"}
    assert set(manifest["compatibility"]["platforms"]) <= {"darwin", "win32", "linux"}
    for option in manifest["user_config"].values():
        assert {"type", "title", "description"} <= set(option)
        assert option["type"] in ("string", "number", "boolean", "directory", "file")


def test_the_extension_launches_its_own_wheel_on_the_chosen_workspace(tmp_path):
    bundle = _bundle(tmp_path)
    manifest = json.loads(bundle.read("manifest.json"))
    args = manifest["server"]["mcp_config"]["args"]
    assert args[:2] == ["--from", "${__dirname}/" + WHEEL]
    assert WHEEL in bundle.namelist()
    assert json.loads(bundle.read("manifest.json"))["version"] == VERSION
    assert args[2:] == ["scholar-agent", "--workspace", "${user_config.workspace}"]
    assert manifest["user_config"]["workspace"]["type"] == "directory"


def test_the_extension_holds_no_key(tmp_path):
    bundle = _bundle(tmp_path)
    text = bundle.read("manifest.json").decode("utf-8")
    manifest = json.loads(text)
    assert "env" not in manifest["server"]["mcp_config"]
    for word in ("API_KEY", "api_key", "token", "secret"):
        assert word not in text, word
    assert not any(option.get("sensitive") for option in manifest["user_config"].values())
