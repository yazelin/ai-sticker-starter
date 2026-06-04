#!/usr/bin/env python3
"""Run all deterministic checks. No API key, no network.

    uv run python client_smoke_test.py
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
TESTS = [
    "tests/test_grid.py",
    "tests/test_chroma.py",
    "tests/test_pack.py",
    "tests/test_gen_fake.py",
]


def main():
    failed = 0
    for t in TESTS:
        print(f"== {t} ==")
        r = subprocess.run([sys.executable, str(ROOT / t)], capture_output=True, text=True)
        sys.stdout.write(r.stdout)
        if r.stderr:
            sys.stderr.write(r.stderr)
        if r.returncode != 0:
            failed += 1
        print()
    if failed:
        print(f"FAIL: {failed} check(s) failed")
        sys.exit(1)
    print("OK: all checks passed")


if __name__ == "__main__":
    main()
