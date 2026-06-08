from backend.database import SessionLocal
from backend.models import Transaction

from backend.ai.ml_model import train_model
from backend.ai.anomaly_model import train_anomaly

import pandas as pd


# =====================================================
# LOAD DATA FROM DATABASE
# =====================================================

def load_transactions():

    db = SessionLocal()

    try:

        data = db.query(Transaction).all()

        if not data:
            print("❌ No transactions found in database")
            return None

        df = pd.DataFrame([
            t.__dict__ for t in data
        ])

        # remove sqlalchemy internal column
        df.drop(
            columns=["_sa_instance_state"],
            errors="ignore",
            inplace=True
        )

        return df

    finally:
        db.close()


# =====================================================
# DATA VALIDATION
# =====================================================

def validate_dataset(df):

    if df is None or df.empty:
        raise ValueError("Dataset is empty")

    required_columns = [
        "amount",
        "country",
        "device",
        "transaction_type",
        "payment_method",
        "is_fraud"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    # remove invalid rows
    df = df[df["amount"] > 0]

    # remove duplicates
    if "transaction_id" in df.columns:
        df = df.drop_duplicates(
            subset=["transaction_id"]
        )

    return df


# =====================================================
# TRAINING PIPELINE
# =====================================================

def main():

    print("\n🚀 Starting AI training pipeline...\n")

    try:

        # =============================================
        # LOAD DATA
        # =============================================

        df = load_transactions()

        if df is None:
            return

        print(f"✅ Loaded {len(df)} transactions")

        # =============================================
        # VALIDATE DATA
        # =============================================

        df = validate_dataset(df)

        print("✅ Dataset validation completed")

        # =============================================
        # FRAUD DISTRIBUTION
        # =============================================

        fraud_count = df["is_fraud"].sum()
        total_count = len(df)

        fraud_ratio = (
            fraud_count / total_count
            if total_count > 0
            else 0
        )

        print(
            f"📊 Fraud ratio: "
            f"{fraud_count}/{total_count} "
            f"({fraud_ratio:.2%})"
        )

        # =============================================
        # TRAIN ML MODEL
        # =============================================

        print("\n🧠 Training ML model...")

        train_model(df)

        print("✅ ML model training completed")

        # =============================================
        # TRAIN ANOMALY MODEL
        # =============================================

        print("\n🔍 Training anomaly detection model...")

        train_anomaly(df)

        print("✅ Anomaly model training completed")

        # =============================================
        # FINISHED
        # =============================================

        print("\n🎉 AI training pipeline finished successfully")

    except Exception as e:

        print("\n❌ Training pipeline failed")
        print("ERROR:", str(e))


# =====================================================
# ENTRYPOINT
# =====================================================

if __name__ == "__main__":
    main()