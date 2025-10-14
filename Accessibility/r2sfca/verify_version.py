"""验证所有文件中的版本号是否一致为 1.1.2"""

import re
import sys


def check_version_in_file(filepath, pattern):
    """检查文件中的版本号"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(pattern, content)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None


def main():
    expected_version = "1.1.2"
    checks = [
        ("setup.py", r'version="([^"]+)"'),
        ("pyproject.toml", r'version\s*=\s*"([^"]+)"'),
        ("r2sfca/__init__.py", r'__version__\s*=\s*"([^"]+)"'),
        ("CHANGELOG.md", r"## \[([^\]]+)\] - 2025-10-14"),
    ]

    print("=" * 60)
    print("Version Consistency Check")
    print("=" * 60)
    print(f"Expected version: {expected_version}\n")

    all_ok = True
    for filepath, pattern in checks:
        version = check_version_in_file(filepath, pattern)

        if version == expected_version:
            print(f"  [OK] {filepath:30s} -> {version}")
        else:
            print(
                f"  [FAIL] {filepath:30s} -> {version} (expected: {expected_version})"
            )
            all_ok = False

    print("\n" + "=" * 60)
    if all_ok:
        print("[SUCCESS] All version checks passed!")
        print("You can now proceed with build and upload.")
        print("=" * 60)
        return 0
    else:
        print("[ERROR] Version mismatch found!")
        print("Please check the files listed above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
