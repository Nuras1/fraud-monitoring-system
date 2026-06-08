import pandas as pd
from sqlalchemy import create_engine

print("Loading SQLite...")

sqlite_engine = create_engine(
    "sqlite:///fraud_monitoring.db"
)

df = pd.read_sql(
    "SELECT * FROM transactions",
    sqlite_engine
)

print(f"Loaded {len(df)} rows")

# ==========================================
# FIX BOOLEAN COLUMNS
# ==========================================

bool_columns = [
    "recipient_is_resident",
    "sender_is_resident",
    "is_fraud"
]

for col in bool_columns:

    if col in df.columns:

        df[col] = (
            df[col]
            .fillna(False)
            .astype(bool)
        )

print("Boolean conversion complete")

# ==========================================
# CONNECT POSTGRES
# ==========================================

postgres_engine = create_engine(
    "postgresql+psycopg2://postgres:admin@localhost:5432/fraud_monitoring"
)

print("Uploading...")

df.to_sql(
    "transactions",
    postgres_engine,
    if_exists="append",
    index=False,
    chunksize=1000
)

print("Migration completed!")