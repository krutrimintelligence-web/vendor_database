import re
from sqlalchemy import Column, Integer, MetaData, String, Table, Text, create_engine

meta = MetaData()
vendors = Table(
    "vendors", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("created_at", String(32)),
    Column("category", String(200), nullable=False),
    Column("name", Text, nullable=False),
    Column("location", Text),
    Column("phone", String(100)),
    Column("notes", Text),
)


def make_engine(url):
    url = re.sub(r"^postgres(ql)?://", "postgresql+psycopg2://", url)
    return create_engine(url, pool_pre_ping=True)
