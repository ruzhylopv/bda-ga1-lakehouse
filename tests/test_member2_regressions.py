"""Runs the existing Member 2 regression script (tests/check_member2.py) under pytest."""
import os
import runpy

from conftest import ROOT


def test_member2_regressions(capsys):
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        runpy.run_path(str(ROOT / "tests" / "check_member2.py"), run_name="__main__")
    finally:
        os.chdir(cwd)
    assert "all targeted checks passed" in capsys.readouterr().out
