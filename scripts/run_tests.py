"""Run every unittest and both legacy script suites; no third-party runner needed."""

from contextlib import redirect_stdout
import importlib.util
import io
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


def run_legacy(module) -> bool:
    """Reject nonzero exits, reported failures, and accidentally empty script suites."""
    captured = io.StringIO()
    with redirect_stdout(captured):
        status = module.main()
    passed = getattr(module, "passed", 0)
    failed = getattr(module, "failed", 0)
    success = status == 0 and passed > 0 and failed == 0
    print(f"{module.__name__}: {passed} passed, {failed} failed", flush=True)
    if not success:
        print(captured.getvalue())
    return success


def main() -> int:
    sys.path.insert(0, str(ROOT))
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    success = result.wasSuccessful() and result.testsRun > 0
    for name in ("test_all", "test_botprotection"):
        spec = importlib.util.spec_from_file_location(name, ROOT / "tests" / (name + ".py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        success = run_legacy(module) and success
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
