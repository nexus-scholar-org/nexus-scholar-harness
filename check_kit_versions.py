#!/usr/bin/env python3
"""Check local vs GitHub kit versions."""

import json
from pathlib import Path
from typing import Optional
import sys

# Try to import httpx for GitHub API calls
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


def get_local_version(kit_name: str) -> Optional[str]:
    """Get version from local pyproject.toml."""
    pyproject_path = Path(f"tools/{kit_name}/pyproject.toml")
    if not pyproject_path.exists():
        return None
    
    content = pyproject_path.read_text()
    for line in content.split("\n"):
        if 'version' in line and '=' in line:
            # Extract version string
            parts = line.split('=')
            if len(parts) >= 2:
                version = parts[1].strip().strip('"').strip("'")
                return version
    return None


def get_github_version(repo: str) -> Optional[str]:
    """Get latest release version from GitHub."""
    if not HAS_HTTPX:
        return None
    
    try:
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        response = httpx.get(url, timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            return data.get('tag_name', 'unknown')
        elif response.status_code == 404:
            return "no-release"
        else:
            return f"error-{response.status_code}"
    except Exception as e:
        return f"error: {str(e)}"


def main():
    print("🔍 Kit Version Comparison Report\n")
    print("=" * 80)
    
    kits = [
        'scholar-search-kit',
        'scholar-pdf-kit',
        'scholar-bib-kit',
        'scholar-graph-kit',
        'scholar-rag-kit',
        'scholar-agent-kit',
    ]
    
    # Collect data
    results = []
    for kit_name in kits:
        local_version = get_local_version(kit_name)
        github_version = None
        status = "✅"
        
        if HAS_HTTPX:
            github_version = get_github_version(f"nexus-scholar-org/{kit_name}")
            if github_version is None:
                status = "⚠️"
            elif local_version != github_version and not (github_version and github_version.startswith("error")):
                status = "⚠️"
        else:
            github_version = "N/A (httpx not installed)"
        
        results.append({
            'kit': kit_name,
            'local': local_version,
            'github': github_version,
            'status': status
        })
    
    # Display table
    print(f"{'Status':<4} {'Kit':<25} {'Local Version':<15} {'GitHub Version':<20}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['status']:<4} {r['kit']:<25} {r['local']:<15} {r['github']:<20}")
    
    print("\n" + "=" * 80)
    
    # Summary
    if not HAS_HTTPX:
        print("\n⚠️  httpx module not installed. Cannot fetch GitHub versions.")
        print("   Install with: pip install httpx")
    else:
        matching = sum(1 for r in results if r['status'] == '✅')
        total = len(results)
        print(f"\n📊 Summary: {matching}/{total} kits up-to-date with GitHub")
    
    # Details on local versions
    print("\n📁 Local Versions:")
    for r in results:
        if r['local']:
            print(f"   • {r['kit']}: {r['local']}")
        else:
            print(f"   • {r['kit']}: NOT FOUND")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
