# run with uv run --no-project --with duckdb --with sqlglot python tests/check_member2.py
import json, ast
from pathlib import Path
from types import SimpleNamespace
import duckdb,sqlglot

notebooks={p.stem:json.loads(p.read_text()) for p in Path('notebooks').glob('0[234]*')}
for name,n in notebooks.items():
 for c in n['cells']:
  s=''.join(c['source'])
  if c['cell_type']!='code':continue
  if s.startswith('%sql'):
   sqlglot.parse(s.split('\n',1)[1],read='databricks')
  else:ast.parse(s)
sqlglot.parse(Path('sql/brand_share_alert.sql').read_text(),read='databricks')
print('notebook Python and SQL syntax passed')

con=duckdb.connect()
con.execute("CREATE MACRO ADD_MONTHS(d,n) AS CAST(d + n * INTERVAL '1 MONTH' AS DATE)")
class Row(SimpleNamespace):
 def __getitem__(self,i):return list(vars(self).values())[i]
class Query:
 def __init__(self,q):
  cursor=con.execute(q);self.names=[d[0] for d in cursor.description];self.rows=cursor.fetchall()
 def first(self):return self.rows[0]
 def collect(self):return [Row(**dict(zip(self.names,r))) for r in self.rows]
 def show(self,**kwargs):
  assert self.rows[0][self.names.index('worst_monthly_rank')]==2,self.rows
  print('monthly rank regression passed: winner can rank second')
class Spark:
 def sql(self,q):return Query(q)
spark=Spark()
exec(''.join(notebooks['04_monitoring']['cells'][10]['source']),{'spark':spark})
con.execute('CREATE SCHEMA bda_gold')
con.execute('CREATE TABLE bda_gold.brand_sales(order_date DATE)')
con.execute("INSERT INTO bda_gold.brand_sales VALUES ('1996-01-01'),('1996-04-01')")
con.execute('CREATE TABLE bda_gold.brand_category_monthly(month_start DATE, category VARCHAR, brand VARCHAR, brand_revenue DECIMAL(18,2), market_share DECIMAL(18,8))')
con.execute("""INSERT INTO bda_gold.brand_category_monthly VALUES
('1996-02-01','TEST','Brand#32',900,0.9),
('1996-02-01','TEST','Brand#33',100,0.1),
('1996-03-01','TEST','Brand#32',400,0.4),
('1996-03-01','TEST','Brand#33',600,0.6)""")
exec(''.join(notebooks['02_gold_layer']['cells'][14]['source']),{'spark':spark})
print('all targeted checks passed')
