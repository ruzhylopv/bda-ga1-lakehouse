# bda-ga1-lakehouse

A Lakehouse migration for **TPC-H** (a wholesale supplier) on Databricks: Bronze, Silver and Gold layers, a validated
pipeline, and answers to the **Brand Manager** business questions, with a dashboard, a monitoring alert and a portable setup.

Group Assignment 1, Big Data Analytics (UCU).

---

## Answers at a glance

Numbers come from the team's executed run on Databricks. Data covers 1992-01-01 to 1998-08-02.

| # | Question | Answer |
|---|---|---|
| Q1 | Total revenue of Brand#32 and its share within its category | **$43.38 B** net revenue. Brand#32 has products in **all 150 categories**; its share ranges from **3.42%** (LARGE BURNISHED BRASS) to **4.63%** (PROMO POLISHED STEEL), **3.98%** overall, i.e. almost exactly the 4% equal split among 25 brands. |
| Q2 | Average margin (list price minus supply cost) for Brand#32 products | **$998.87** per unit, over **39,792** products (all have supplier offers). |
| Q3 | Brand with the largest share within its category, and is it stable? | **Brand#33 in ECONOMY BRUSHED BRASS, 4.92%** all-time. **Stable**: over 78 complete months its share stays within 3.74% to 6.20% (range 2.46 pp, below our 5 pp rule). Its monthly rank, however, moves between 1st and 15th: leaders are separated by hundredths of a point. |
| Q4 | Products whose sale price differs from list price by more than 15% | **0 of 1,000,000**, so no concentration in any brand or category. This is a property of TPC-H: `l_extendedprice = l_quantity * p_retailprice`, so the deviation equals the discount, which never exceeds 10%. |
| Monitoring | Brand revenue and share within category over time, alert on a shift | Alert fires when Brand#32 loses **>= 5 pp** in a category versus the previous complete month. Latest complete month (1998-07): **0 alerts**, largest drop -1.67 pp (SMALL POLISHED TIN). |

## Architecture

```
samples.tpch ──► bda_bronze ──► bda_silver ──► bda_gold ──► dashboard / notebook / SQL alert
 (source)        as-is +        normalized,     brand facts,
                 ingestion_ts   quality rules,  monthly shares,
                                quarantine      monitoring
                     └──────── 03_validation checks every layer; critical failures stop the run ────────┘
```

| Layer | Schema | What it holds | Notebook |
|---|---|---|---|
| Bronze | `bda_bronze` | The 8 TPC-H tables unchanged, plus `ingestion_timestamp` | `00_bronze_layer_ingestion` |
| Silver | `bda_silver` | Normalized TPC-H model; parts with empty brand/manufacturer go to `part_quarantine`; `NOT NULL` + `CHECK` constraints on `part`; `lineitem` gets derived `revenue` and `margin` | `01_silver_layer` |
| Gold | `bda_gold` | `brand_sales` (one row per sale line, 30 M), `brand_category_monthly` (dense brand x category x month, 300 K), `part_list_margin`, `price_deviation_products`, `brand_monitoring`, `brand_share_change_explanation`, `validation_results`, `run_audit` | `02_gold_layer`, `04_monitoring` |

### Silver ER diagram

The ER diagram of the Silver tables is shown in the presentation. Keys are logical TPC-H keys; uniqueness and the foreign
keys used by the analysis are enforced by checks in `03_validation`.

**Normal form.** Silver keeps the TPC-H schema, which is in 3NF by design: one table per entity, keyed by its natural key;
composite keys only for `partsupp (ps_partkey, ps_suppkey)` and `lineitem (l_orderkey, l_linenumber)`; descriptive
attributes live only in their own entity. Verified in the submitted run: 18/18 Silver checks (keys unique and non-null,
no orphan foreign keys on lineitem -> orders/part/partsupp and partsupp -> part/supplier).
**Documented exception:** `lineitem.revenue` and `lineitem.margin` are derived convenience columns: recomputable from
source columns and validated against the source by the revenue reconciliation.
`notebooks/08_silver_normal_form_checks` adds data-driven functional-dependency tests for 1NF/2NF/3NF; it is optional
and **was not part of the submitted run**.

## Business definitions

Every query uses these definitions (see `02_gold_layer`).

| Concept | Definition |
|---|---|
| Revenue (net) | `l_extendedprice * (1 - l_discount)`, excluding tax |
| List price | `p_retailprice` (unit price) |
| Supply cost | `ps_supplycost` of the exact (part, supplier) pair |
| List-price margin | `p_retailprice - ps_supplycost` |
| Average margin | average over a product's supplier offers first, then equal-weight average over products (no double counting across suppliers) |
| Actual unit price | net revenue / `l_quantity` |
| Price deviation | `abs(actual_unit_price - p_retailprice) / p_retailprice`; a product is affected if any sale line has deviation > 0.15 |
| Reporting date | `o_orderdate`, truncated to month |
| Category | full `p_type` value (150 categories) |
| Market share | brand revenue in category / total category revenue (all brands) |
| Complete month | every month except the first and last observed month (data ends 1998-08-02) |
| Stable share | monthly share range <= 5 pp over complete months (project assumption) |
| Alert | Brand#32 share in a category falls by >= 5 pp vs. the previous complete, consecutive month |

## Validation

How we decided to validate: prove trust layer by layer, persist every result, and show that the checks catch real errors.

| Phase | Checks | What is checked |
|---|---|---|
| Bronze vs. source | 32 | row counts; data equality in both directions (`EXCEPT ALL`); identical schema |
| Silver | 18 | key uniqueness and nulls, foreign keys, non-empty brand/manufacturer, positive price and quantity, non-null money columns |
| Reconciliation | 2 | Bronze `part` = Silver `part` + `part_quarantine`, in both directions |
| Gold | 15 | sale-line keys match Silver exactly; revenue Bronze = Silver = Gold within $0.01; monthly totals = detail; shares sum to 1 and lie in [0, 1]; margin matches an independent Silver reference; monitoring grain and share-change identity |

Submitted run: **67/67 passed**. Results are appended to `bda_gold.validation_results`; `02_gold_layer` also refuses to
build on bad input and records input table versions in `bda_gold.run_audit`. The error demonstration injects 5 faults
(empty brand, duplicate supplier offer, missing (part, supplier) reference, modified revenue, null quantity) into temporary
views: all 5 are detected. The alert logic is tested with 7 synthetic scenarios (-4.99 pp, -5 pp, -6 pp, +6 pp,
incomplete month, missing baseline, unchanged).

## Run it on a Databricks workspace

Developed on Databricks Free Edition with serverless compute.

1. **Get the code:** *Workspace > Create > Git folder*, paste this repo URL.
2. **Run the pipeline:** open `notebooks/06_run_pipeline`, check the two widgets, *Run all*.
   It runs `00` -> `01` -> `05` (which runs `02`, then `04`, which runs `03` validation twice).
3. **See the answers:**
   - `notebooks/07_business_dashboard`: interactive charts for Q1 to Q4, monitoring and validation;
   - `dashboards/brand_manager.lvdash.json`: *Dashboards > Create > Import dashboard from file* (3 pages).
4. **Alert:** create a Databricks SQL alert from `sql/brand_share_alert.sql`, condition `affected_category_count > 0`,
   schedule daily, notify your user. Check the coverage columns before reading a zero.

### Parameters (portability)

The team only had pre-production data, so nothing environment-specific is hardcoded. Every pipeline notebook reads two widgets,
and the runner notebooks pass them to their children:

| Widget | Default | Change it when |
|---|---|---|
| `catalog` | `workspace` | your workspace uses another Unity Catalog catalog (e.g. `dev`, `preprod`) |
| `source_schema` | `samples.tpch` | the TPC-H source lives elsewhere, e.g. `preprod.tpch` |

Schema names are fixed and prefixed (`bda_bronze`, `bda_silver`, `bda_gold`) so they do not collide with other projects in
the same catalog. The same parameters can be set as job parameters if the notebook is scheduled as a Databricks Job.
The TPC-H README cell is optional and is skipped on workspaces without `/dbfs/databricks-datasets`.

## Local development (uv)

The pipeline runs on Databricks; locally you only need [uv](https://docs.astral.sh/uv/) for tooling and tests.

```bash
uv sync                                     # Python + dev tools from uv.lock
uv run pytest                               # tests, no Spark or cluster needed
```

The tests fake the Gold tables in DuckDB and transpile the Databricks SQL with sqlglot. They cover:
notebook syntax (Python and `%sql` cells), portability rules (no hardcoded catalog or source, parameters forwarded to
child notebooks), every dashboard query, the alert firing on a synthetic drop, notebook 07 end to end, the dashboard and
notebook 07 using exactly the SQL in `sql/dashboard/`, and Member 2's regression script (`tests/check_member2.py`).

## Repository layout

```
notebooks/
  00_bronze_layer_ingestion   01_silver_layer        02_gold_layer
  03_validation               04_monitoring          05_run_member2 (Gold + monitoring runner)
  06_run_pipeline (entry point)                      07_business_dashboard
  08_silver_normal_form_checks (optional)
dashboards/brand_manager.lvdash.json   Databricks dashboard
sql/brand_share_alert.sql              alert query
sql/dashboard/*.sql                    dashboard datasets (same SQL in notebook 07)
tests/                                 local test suite
```

## Team

| Member | Role | Responsibilities |
|---|---|---|
| Member 1 | Data Engineer | Bronze (as-is + metadata) and Silver (normalized, quality-enforced) layers, Silver ER diagram, Jobs/Pipelines |
| Member 2 | Analytics Engineer | Gold layer for the Brand Manager questions, validation rules across all layers, monitoring and alerting |
| Member 3 | BI Analyst / DevOps | Public repo with uv, README, portability; visualizations (notebook + dashboard); presentation and demo |

## Challenges

- **Q4 returned zero.** Explained by how TPC-H generates prices (deviation = discount <= 10%) rather than tuning the threshold.
- **Partial boundary months.** 1998-08 has 2 days of data; boundary months are excluded from stability and alerts.
- **Near-ties between leaders.** Ranking uses unrounded shares; a regression test protects the monthly-rank logic.
- **30 M-row scans.** Answers read the dense 300 K-row monthly table instead of the sales fact.
- **Derived columns in Silver.** Kept as a documented exception, reconciled against the source.
- **Hardcoded workspace.** Catalog and source location became parameters, guarded by tests.

## License

MIT, see [LICENSE](LICENSE).
