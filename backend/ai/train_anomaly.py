import pandas as pd

from backend.ai.anomaly_model import (
    train_anomaly
)

print("\n📂 Loading dataset...")

df = pd.read_csv(
    "transactions.csv"
)

print(
    f"✅ Loaded {len(df)} transactions"
)

train_anomaly(df)

print(
    "\n✅ Anomaly model trained"
)