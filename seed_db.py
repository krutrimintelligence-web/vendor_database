"""One-time import of Vendor_List.xls into the database in DATABASE_URL.
Usage: DATABASE_URL=... python seed_db.py Vendor_List.xls [--force]
(--force deletes existing rows first). Needs: pip install xlrd pandas sqlalchemy psycopg2-binary"""
import os, sys
import pandas as pd
from sqlalchemy import delete, func, insert, select
from db import make_engine, meta, vendors

src = next((a for a in sys.argv[1:] if not a.startswith("--")), "Vendor_List.xls")
df = pd.read_excel(src, engine="xlrd", dtype=str).fillna("")
df.columns = ["ts", "category", "name", "location", "phone", "notes"]
for c in df.columns:
    df[c] = df[c].map(lambda s: " ".join(str(s).split()))
df["ts"] = pd.to_datetime(df["ts"].str.replace(r"\s*GMT.*$", "", regex=True),
                          format="%Y/%m/%d %I:%M:%S %p", errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%S").fillna("")
df["phone"] = df["phone"].str.replace(r"\.0$", "", regex=True)

eng = make_engine(os.environ.get("DATABASE_URL", "sqlite:///vendors.db"))
meta.create_all(eng)
with eng.begin() as con:
    n = con.execute(select(func.count()).select_from(vendors)).scalar()
    if n and "--force" not in sys.argv:
        sys.exit(f"Table already has {n} rows; use --force to replace them.")
    con.execute(delete(vendors))
    con.execute(insert(vendors), [dict(created_at=r.ts, category=r.category, name=r.name, location=r.location,
                                       phone=r.phone, notes=r.notes) for r in df.itertuples()])
print(len(df), "vendors imported")
