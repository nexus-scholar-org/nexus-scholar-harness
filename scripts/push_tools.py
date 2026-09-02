"""
Push each toolkit from tools/ to its respective GitHub repository in nexus-scholar-org.
"""
import json
import subprocess
import shutil
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / ".agents/plugins/nexus-scholar/plugins.json"

plugins_data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
plugins = plugins_data.get("plugins", [])

print(f"Found {len(plugins)} toolkits to push:")

for p in plugins:
    name = p["name"]
    repo_url = p["repo"]
    tool_dir = REPO_ROOT / "tools" / name

    if not tool_dir.exists():
        print(f"⚠️  {name}: directory {tool_dir} does not exist, skipping.")
        continue

    print(f"\n🚀 Syncing {name} -> {repo_url} ...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # 1. Clone the existing remote repo into tmp
        clone_res = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(tmp_path)],
            capture_output=True,
            text=True
        )
        if clone_res.returncode != 0:
            print(f"  Clone failed ({clone_res.stderr.strip()}), initializing fresh repo...")
            subprocess.run(["git", "init", "-b", "main", str(tmp_path)], check=True)
            subprocess.run(["git", "-C", str(tmp_path), "remote", "add", "origin", repo_url], check=True)

        # 2. Copy all files from tools/<name> into tmp_path (excluding .git, __pycache__, .venv, .pytest_cache)
        for item in tool_dir.iterdir():
            if item.name in [".git", "__pycache__", ".venv", ".pytest_cache", ".ruff_cache", ".cache"]:
                continue
            dest = tmp_path / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".venv", ".cache"))
            else:
                shutil.copy2(item, dest)

        # 3. Commit and push
        subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
        status = subprocess.run(["git", "-C", str(tmp_path), "status", "--porcelain"], capture_output=True, text=True, check=True)
        
        if not status.stdout.strip():
            print(f"  ✓ {name} is already up to date with remote.")
        else:
            commit_res = subprocess.run(
                ["git", "-C", str(tmp_path), "commit", "-m", f"feat({name}): synchronize toolkit with nexus-scholar monorepo"],
                capture_output=True,
                text=True
            )
            print(f"  Committed: {commit_res.stdout.splitlines()[0] if commit_res.stdout else 'Done'}")
            
            push_res = subprocess.run(
                ["git", "-C", str(tmp_path), "push", "origin", "main"],
                capture_output=True,
                text=True
            )
            if push_res.returncode == 0:
                print(f"  ✅ Successfully pushed {name} to {repo_url}")
            else:
                print(f"  ❌ Push failed for {name}: {push_res.stderr.strip()}")

print("\n🎉 All toolkits processed!")
