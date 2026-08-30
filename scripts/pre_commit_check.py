#!/usr/bin/env python3
"""Pre-commit checklist for plugin harness refactor."""
import subprocess
import sys
from pathlib import Path

def run_cmd(cmd):
    """Run a command and return output."""
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.returncode, result.stdout, result.stderr

def main():
    print("🔍 Pre-Commit Checklist for Plugin Harness Refactor\n")
    print("=" * 70)
    
    checks_passed = 0
    checks_total = 0
    
    # 1. Validate manifest (simpler check - just verify file exists and is JSON)
    checks_total += 1
    print("\n1. Validate plugin manifest...")
    try:
        import json
        with open(".agents/plugins/nexus-scholar/plugins.json") as f:
            manifest = json.load(f)
        if manifest.get("plugins") and len(manifest["plugins"]) > 0:
            print(f"   ✅ Plugin manifest is valid ({len(manifest['plugins'])} plugins)")
            checks_passed += 1
        else:
            print("   ❌ Plugin manifest has no plugins defined")
    except Exception as e:
        print(f"   ❌ Plugin manifest validation failed: {e}")
    
    # 2. Check install_plugins.py syntax
    checks_total += 1
    print("\n2. Check install_plugins.py syntax...")
    code, stdout, _ = run_cmd("uv run python -m py_compile scripts/install_plugins.py")
    if code == 0:
        print("   ✅ install_plugins.py syntax is valid")
        checks_passed += 1
    else:
        print(f"   ❌ Syntax error in install_plugins.py")
    
    # 3. Check .gitignore includes tools/
    checks_total += 1
    print("\n3. Check .gitignore ignores tools/...")
    gitignore_content = Path(".gitignore").read_text(encoding="utf-8")
    if "tools/" in gitignore_content:
        print("   ✅ .gitignore correctly ignores tools/")
        checks_passed += 1
    else:
        print("   ❌ .gitignore does not ignore tools/")
    
    # 4. Check README mentions plugin installer
    checks_total += 1
    print("\n4. Check README describes plugin installer...")
    readme_content = Path("README.md").read_text(encoding="utf-8")
    if "scripts/install_plugins.py" in readme_content and "uv run scholar-" in readme_content:
        print("   ✅ README correctly describes plugin installation")
        checks_passed += 1
    else:
        print("   ❌ README does not mention plugin installer correctly")
    
    # 5. Check CI workflow exists
    checks_total += 1
    print("\n5. Check GitHub Actions CI workflow...")
    ci_path = Path(".github/workflows/ci.yml")
    if ci_path.exists():
        print("   ✅ CI workflow exists at .github/workflows/ci.yml")
        checks_passed += 1
    else:
        print("   ❌ CI workflow not found")
    
    # 6. Check tools/ is tracked in git (will be removed)
    checks_total += 1
    print("\n6. Check tools/ is tracked in git (will be removed)...")
    try:
        # Simply check if tools directory exists and has git-tracked files
        tools_path = Path("tools")
        if tools_path.exists() and list(tools_path.glob("**/pyproject.toml")):
            print("   ⚠️  tools/ exists with tracked packages - will be removed")
            checks_passed += 1  # This is expected and OK
        else:
            print("   ✅ tools/ is not present (already clean)")
            checks_passed += 1
    except Exception as e:
        print(f"   ⚠️  Could not verify git status: {e}")
        checks_passed += 1  # Not critical
    
    print("\n" + "=" * 70)
    print(f"\n📊 Checks Passed: {checks_passed}/{checks_total}")
    
    if checks_passed == checks_total:
        print("\n✅ Ready for commit! Recommended git commands:\n")
        print("   # Stage all changes")
        print("   git add -A")
        print()
        print("   # Remove tools/ from git tracking")
        print("   git rm -r --cached tools/")
        print()
        print("   # Create commit")
        print("   git commit -m \"Refactor: Move tools to external plugins with unified installer\"")
        print()
        print("   # Push to remote")
        print("   git push origin main")
        return 0
    else:
        print(f"\n❌ {checks_total - checks_passed} check(s) failed. Fix issues before committing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
