"""Dependency-free runner for tests/test_engine.py (works without pytest):  python tests/run_all.py"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import test_engine  # noqa: E402

failed = 0
for name in sorted(n for n in dir(test_engine) if n.startswith("test_")):
    try:
        getattr(test_engine, name)()
        print(f"PASS  {name}")
    except Exception as exc:  # noqa: BLE001
        failed += 1
        print(f"FAIL  {name}: {type(exc).__name__}: {exc}")
print(f"\n{'ALL PASSED' if not failed else str(failed) + ' FAILED'}")
sys.exit(1 if failed else 0)
