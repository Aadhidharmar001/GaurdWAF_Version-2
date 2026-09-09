"""
GuardWAF Automated Release Builder.
Builds source distribution (sdist) and wheel (.whl) packages into the dist/ directory.
"""

import os
import shutil
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    print("=================================================================")
    print("🛡️  GUARdWAF AUTOMATED RELEASE BUILDER")
    print("=================================================================")

    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dist_dir = os.path.join(root_dir, "dist")

    # Clean existing dist/ directory
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)

    # Run python -m build
    cmd = [sys.executable, "-m", "build", root_dir]
    print(f"▶ Building GuardWAF package artifacts: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")

    if res.returncode != 0:
        print(f"❌ BUILD FAILED:\n{res.stderr}")
        sys.exit(1)

    artifacts = os.listdir(dist_dir)
    print(f"✅ BUILD SUCCESSFUL: Generated {len(artifacts)} release artifact(s) in 'dist/':")
    for a in artifacts:
        print(f"   - dist/{a}")

    print("=================================================================")


if __name__ == "__main__":
    main()
