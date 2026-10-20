"""
tests/run_all.py - run every test suite in one go.

    python3 tests/run_all.py
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUITES = ["test_engine.py", "test_db.py", "test_compliance.py", "test_api.py"]


def main() -> int:
    failed = []
    total = 0

    for suite in SUITES:
        print(f"\n\033[1m── {suite} {'─' * (54 - len(suite))}\033[0m")
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, suite)],
            capture_output=True, text=True,
        )
        output = result.stdout + result.stderr
        for line in output.splitlines():
            if line.startswith("  ok -") or "passed" in line or "FAIL" in line:
                print(line)
        if "passed" in output:
            for line in output.splitlines():
                if "tests passed" in line:
                    total += int(line.split()[1])
        if result.returncode != 0:
            failed.append(suite)

    print()
    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1
    print(f"All suites passed — {total} checks in total.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
