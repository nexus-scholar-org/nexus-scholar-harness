#!/usr/bin/env python3
"""Validate plugin manifest structure."""
import json
import sys
from pathlib import Path

def validate_manifest():
    manifest_path = Path(".agents/plugins/nexus-scholar/plugins.json")
    
    if not manifest_path.exists():
        print(f"❌ Manifest not found at {manifest_path}")
        sys.exit(1)
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    plugins = manifest.get("plugins", [])
    if not plugins:
        print("❌ No plugins defined in manifest")
        sys.exit(1)
    
    print(f"✅ Plugin manifest valid: {len(plugins)} plugins")
    for plugin in plugins:
        required = {"name", "repo", "default_rev", "console_script"}
        if not required.issubset(plugin.keys()):
            print(f"  ❌ {plugin.get('name')}: missing required fields")
            sys.exit(1)
        print(f"  ✅ {plugin['name']}")
    
    print("✅ All plugins validated successfully")
    return 0

if __name__ == "__main__":
    sys.exit(validate_manifest())
