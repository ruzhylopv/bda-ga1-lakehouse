"""Local, Spark-free test harness: Gold tables are faked in DuckDB and Databricks SQL is transpiled with sqlglot."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import duckdb
import pytest
import sqlglot

ROOT = Path(__file__).resolve().parents[1]


def to_duckdb(sql: str) -> str:
    return ";\n".join(e.sql(dialect="duckdb") for e in sqlglot.parse(sql, read="databricks") if e is not None)


class FakeDataFrame:
    def __init__(self, con, sql):
        self._df = con.execute(to_duckdb(sql)).df()

    def toPandas(self):
        return self._df


class FakeSpark:
    def __init__(self, con):
        self.con = con

    def sql(self, sql):
        if sql.strip().upper().startswith("USE CATALOG"):
            return None
        return FakeDataFrame(self.con, sql)


class FakeWidgets:
    def __init__(self):
        self.values = {}

    def text(self, name, default, label=None):
        self.values.setdefault(name, default)

    dropdown = lambda self, name, default, choices, label=None: self.text(name, default)

    def get(self, name):
        return self.values[name]


class FakeDbutils:
    def __init__(self):
        self.widgets = FakeWidgets()


def _months(start: date, n: int):
    y, m = start.year, start.month
    for _ in range(n):
        yield date(y, m, 1)
        m += 1
        if m == 13:
            y, m = y + 1, 1


@pytest.fixture()
def gold():
    """Tiny but structurally faithful copy of the bda_gold tables."""
    con = duckdb.connect()
    con.execute("CREATE SCHEMA bda_gold")
    brands, cats = ["Brand#32", "Brand#33", "Brand#11"], ["SMALL TIN", "LARGE BRASS"]
    months = list(_months(date(1996, 1, 1), 8))
    rows = []
    for i, mth in enumerate(months):
        for c, cat in enumerate(cats):
            revs = {b: 100 + 10 * j + 5 * c + (i % 3) * (j + 1) for j, b in enumerate(brands)}
            if i == 4 and cat == "SMALL TIN":
                revs["Brand#32"] = 20  # a sharp drop -> alert scenario
            tot = sum(revs.values())
            for b, r in revs.items():
                rows.append((mth, cat, b, r, tot, r / tot))
    con.execute("CREATE TABLE bda_gold.brand_category_monthly(month_start DATE, category VARCHAR, brand VARCHAR,"
                " brand_revenue DECIMAL(18,2), category_revenue DECIMAL(18,2), market_share DECIMAL(18,8))")
    con.executemany("INSERT INTO bda_gold.brand_category_monthly VALUES (?,?,?,?,?,?)", rows)
    con.execute("""CREATE TABLE bda_gold.brand_monitoring AS
        SELECT *, LAG(market_share) OVER w AS previous_market_share,
               (market_share - LAG(market_share) OVER w) * 100 AS share_change_percentage_points,
               month_start > DATE '1996-01-01' AND month_start < DATE '1996-08-01' AS is_complete_month,
               month_start > DATE '1996-02-01' AND month_start < DATE '1996-08-01' AS is_comparable_month
        FROM bda_gold.brand_category_monthly WINDOW w AS (PARTITION BY brand, category ORDER BY month_start)""")
    con.execute("""CREATE TABLE bda_gold.brand_share_change_explanation AS
        SELECT month_start, brand, category, 0.5 * share_change_percentage_points AS brand_revenue_effect_pp,
               0.5 * share_change_percentage_points AS category_revenue_effect_pp,
               share_change_percentage_points AS actual_share_change_pp
        FROM bda_gold.brand_monitoring WHERE is_comparable_month""")
    con.execute("""CREATE TABLE bda_gold.part_list_margin AS
        SELECT i AS part_key, ['Brand#32','Brand#33','Brand#11'][1 + i % 3] AS brand,
               ['SMALL TIN','LARGE BRASS'][1 + i % 2] AS category, 4 AS supplier_offer_count,
               CAST(900 + i AS DECIMAL(18,2)) AS average_list_unit_margin
        FROM range(30) t(i)""")
    con.execute("""CREATE TABLE bda_gold.brand_sales AS
        SELECT i AS part_key, 'Brand#32' AS brand, 'SMALL TIN' AS category, (i % 11) / 100.0 AS price_deviation_ratio
        FROM range(200) t(i)""")
    con.execute("""CREATE VIEW bda_gold.price_deviation_products AS
        SELECT part_key, brand, category, COUNT(*) AS anomalous_line_count, MAX(price_deviation_ratio) AS m
        FROM bda_gold.brand_sales WHERE price_deviation_ratio > 0.15 GROUP BY ALL""")
    con.execute("""CREATE TABLE bda_gold.validation_results AS
        SELECT 'run1' AS run_id, TIMESTAMP '2026-10-07 18:42:00' AS checked_at, phase, 'c' || i AS check_name,
               true AS passed, true AS is_critical
        FROM (VALUES ('bronze'), ('silver'), ('gold')) p(phase), range(3) t(i)""")
    yield con
    con.close()


@pytest.fixture()
def fake_env(gold):
    displayed = []
    return {"spark": FakeSpark(gold), "dbutils": FakeDbutils(),
            "displayHTML": displayed.append, "display": displayed.append, "_displayed": displayed}


def notebook(name: str) -> dict:
    return json.loads((ROOT / "notebooks" / f"{name}.ipynb").read_text())
