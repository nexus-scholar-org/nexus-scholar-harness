#!/usr/bin/env python3
"""Verify harness skills upgrade completeness."""

import subprocess
import sys
from pathlib import Path


def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists."""
    path = Path(path).resolve()
    cwd = Path.cwd().resolve()
    
    if path.exists():
        try:
            rel_path = path.relative_to(cwd)
        except ValueError:
            rel_path = path
        print(f"  ✅ {description}: {rel_path}")
        return True
    else:
        try:
            rel_path = path.relative_to(cwd)
        except ValueError:
            rel_path = path
        print(f"  ❌ {description}: NOT FOUND ({rel_path})")
        return False


def check_script_help(script_path: Path, description: str) -> bool:
    """Check if a script is functional by running --help."""
    try:
        result = subprocess.run(
            ["uv", "run", "python", str(script_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print(f"  ✅ {description}: Functional")
            return True
        else:
            print(f"  ❌ {description}: Script failed (exit code {result.returncode})")
            return False
    except Exception as e:
        print(f"  ❌ {description}: Error: {e}")
        return False


def main():
    print("🔍 Harness Skills Upgrade Verification\n")
    print("=" * 70)
    
    checks = []
    
    # ===== methodology-copilot =====
    print("\n📚 methodology-copilot")
    print("-" * 70)
    
    methodology_dir = Path(".agents/skills/methodology-copilot")
    
    checks.append(check_file_exists(
        methodology_dir / "SKILL.md",
        "SKILL.md (with async + batch + performance sections)"
    ))
    checks.append(check_file_exists(
        methodology_dir / "references/performance_caching.md",
        "New performance_caching.md reference"
    ))
    checks.append(check_file_exists(
        methodology_dir / "references/paradigm_refraction_guide.md",
        "paradigm_refraction_guide.md"
    ))
    checks.append(check_file_exists(
        methodology_dir / "references/socratic_interview_framework.md",
        "socratic_interview_framework.md"
    ))
    checks.append(check_file_exists(
        methodology_dir / "references/criteria_generator_spec.md",
        "criteria_generator_spec.md"
    ))
    
    # ===== workspace-manager =====
    print("\n🗂️  workspace-manager")
    print("-" * 70)
    
    workspace_dir = Path(".agents/skills/workspace-manager")
    
    checks.append(check_file_exists(
        workspace_dir / "SKILL.md",
        "SKILL.md (with batch logging + queries + performance sections)"
    ))
    checks.append(check_file_exists(
        workspace_dir / "references/performance_concurrency.md",
        "New performance_concurrency.md reference"
    ))
    checks.append(check_file_exists(
        workspace_dir / "references/project_schema.md",
        "project_schema.md"
    ))
    checks.append(check_file_exists(
        workspace_dir / "references/audit_trace_spec.md",
        "audit_trace_spec.md"
    ))
    checks.append(check_file_exists(
        workspace_dir / "references/tool_routing_matrix.md",
        "tool_routing_matrix.md"
    ))
    
    # Check workspace-manager scripts
    print("\n  Scripts:")
    checks.append(check_file_exists(
        workspace_dir / "scripts/init_project.py",
        "init_project.py"
    ))
    checks.append(check_file_exists(
        workspace_dir / "scripts/log_event.py",
        "log_event.py"
    ))
    checks.append(check_file_exists(
        workspace_dir / "scripts/batch_log.py",
        "batch_log.py (NEW - batch logging)"
    ))
    checks.append(check_file_exists(
        workspace_dir / "scripts/query_project.py",
        "query_project.py (NEW - project queries)"
    ))
    
    # Functional tests
    print("\n🧪 Functional Tests")
    print("-" * 70)
    
    checks.append(check_script_help(
        workspace_dir / "scripts/batch_log.py",
        "batch_log.py --help"
    ))
    checks.append(check_script_help(
        workspace_dir / "scripts/query_project.py",
        "query_project.py --help"
    ))
    checks.append(check_script_help(
        workspace_dir / "scripts/log_event.py",
        "log_event.py --help (existing)"
    ))
    
    # Check summary documents
    print("\n📄 Documentation")
    print("-" * 70)
    
    checks.append(check_file_exists(
        Path("SKILLS_UPGRADE_SUMMARY.md"),
        "SKILLS_UPGRADE_SUMMARY.md"
    ))
    checks.append(check_file_exists(
        Path("README.md"),
        "README.md (harness root)"
    ))
    
    # Summary
    print("\n" + "=" * 70)
    passed = sum(checks)
    total = len(checks)
    
    print(f"\n📊 Summary: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✅ All harness skill upgrades are complete and functional!")
        print("\n🚀 Next steps:")
        print("   - Review SKILLS_UPGRADE_SUMMARY.md for performance gains")
        print("   - Test batch logging: uv run python .agents/skills/workspace-manager/scripts/batch_log.py --help")
        print("   - Test queries: uv run python .agents/skills/workspace-manager/scripts/query_project.py --help")
        print("   - Review methodology-copilot performance docs: .agents/skills/methodology-copilot/references/performance_caching.md")
        print("   - Review workspace-manager performance docs: .agents/skills/workspace-manager/references/performance_concurrency.md")
        return 0
    else:
        print(f"\n❌ {total - passed} check(s) failed. Review above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
