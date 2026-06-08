import pandas as pd

from sqlalchemy import create_engine


# =====================================================
# LOAD CSV
# =====================================================

print("\n📂 Loading CSV...")

df = pd.read_csv(
    "transactions.csv"
)

print(
    f"✅ Loaded {len(df)} transactions"
)

# =====================================================
# SQLITE CONNECTION
# =====================================================

engine = create_engine(
    "sqlite:///fraud_monitoring.db"
)

# =====================================================
# IMPORT TO DATABASE
# =====================================================

df.to_sql(

    "transactions",

    engine,

    if_exists="append",

    index=False
)

print(
    "\n✅ Transactions imported "
    "to SQLite database"
)