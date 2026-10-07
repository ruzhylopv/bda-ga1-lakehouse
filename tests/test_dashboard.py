import json
from pathlib import Path

import plotly.graph_objects as go
import pytest
import sqlglot

from conftest import ROOT, notebook, to_duckdb

SQL_FILES = sorted((ROOT / "sql" / "dashboard").glob("*.sql"))


def test_notebook_and_dashboard_use_the_same_sql():
    """sql/dashboard/*.sql is the source of truth for notebook 07 and the Databricks dashboard."""
    ns = {}
    src = "".join(notebook("07_business_dashboard")["cells"][2]["source"])
    exec(src, ns)
    lvdash = json.loads((ROOT / "dashboards" / "brand_manager.lvdash.json").read_text())
    datasets = {d["name"]: "".join(d["queryLines"]).strip() for d in lvdash["datasets"]}
    for path in SQL_FILES:
        name = path.stem.split("_", 1)[1]
        sql = path.read_text().strip()
        assert ns["QUERIES"][name] == sql, f"notebook 07 differs from {path.name}"
        assert datasets[name] == sql, f"dashboard dataset differs from {path.name}"


@pytest.mark.parametrize("path", SQL_FILES, ids=lambda p: p.name)
def test_dashboard_sql_parses_as_databricks(path: Path):
    assert sqlglot.parse_one(path.read_text(), read="databricks") is not None


@pytest.mark.parametrize("path", SQL_FILES, ids=lambda p: p.name)
def test_dashboard_sql_runs_on_fake_gold(gold, path: Path):
    rows = gold.execute(to_duckdb(path.read_text())).fetchall()
    assert rows, f"{path.name} returned no rows"


def test_alert_fires_on_synthetic_drop(gold):
    sql = (ROOT / "sql" / "dashboard" / "08_monitoring_latest_change.sql").read_text()
    sql = sql.replace("month_start = (", "month_start = DATE '1996-05-01' OR month_start = (", 1)
    statuses = {r[-1] for r in gold.execute(to_duckdb(sql)).fetchall()}
    assert "ALERT" in statuses


def test_dashboard_notebook_runs_end_to_end(fake_env, monkeypatch):
    monkeypatch.setattr(go.Figure, "show", lambda self, *a, **k: None)
    ns = dict(fake_env)
    for cell in notebook("07_business_dashboard")["cells"]:
        src = "".join(cell["source"])
        if cell["cell_type"] == "code" and not src.startswith("%"):
            exec(compile(src, "07_business_dashboard", "exec"), ns)
    assert len(ns["QUERIES"]) == len(SQL_FILES)
    assert fake_env["_displayed"], "KPI tiles / tables were not displayed"
