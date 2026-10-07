"""Portability guards: no hardcoded catalog or source data location in pipeline notebooks."""
import ast
import json
import re

import pytest
import sqlglot

from conftest import ROOT

NOTEBOOKS = sorted((ROOT / "notebooks").glob("0*.ipynb"))


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_no_hardcoded_catalog_or_source(path):
    text = "".join("".join(c["source"]) for c in json.loads(path.read_text())["cells"])
    assert not re.search(r"USE CATALOG\s+workspace\b", text)
    assert "samples.tpch." not in text, "source data must come from the source_schema widget"
    assert "/Users/" not in text and "/Workspace/" not in text, "no absolute personal workspace paths"


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_notebook_cells_parse(path):
    for c in json.loads(path.read_text())["cells"]:
        src = "".join(c["source"])
        if c["cell_type"] != "code" or not src.strip():
            continue
        if src.startswith("%sql"):
            sqlglot.parse(src.split("\n", 1)[1], read="databricks")
        elif src.startswith("%"):
            continue
        else:
            ast.parse(src)


@pytest.mark.parametrize("path", [p for p in NOTEBOOKS if p.stem[:2] in {"00", "01", "03", "04", "05", "06"}], ids=lambda p: p.name)
def test_pipeline_notebooks_take_catalog_and_source_widgets(path):
    text = path.read_text()
    assert 'widgets.text(\\"catalog\\"' in text
    if path.stem[:2] in {"00", "03", "04", "05", "06"}:
        assert 'widgets.text(\\"source_schema\\"' in text


def test_child_runs_forward_parameters():
    for path in NOTEBOOKS:
        for c in json.loads(path.read_text())["cells"]:
            for line in "".join(c["source"]).splitlines():
                if "dbutils.notebook.run(" in line:
                    assert re.search(r"dbutils\.notebook\.run\([^,]+,\s*0,\s*\S", line), f"{path.name}: {line.strip()}"
