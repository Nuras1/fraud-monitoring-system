import pandas as pd
from backend.database import SessionLocal
from backend.models import Transaction


# =====================================================
# EXPORT DATABASE TO CSV
# =====================================================

def export_transactions():

    db = SessionLocal()

    try:

        print("\n📂 Loading transactions from database...")

        transactions = db.query(Transaction).all()

        # =============================================
        # EMPTY DATABASE CHECK
        # =============================================

        if not transactions:

            print("❌ No transactions found")

            return

        # =============================================
        # CONVERT TO DATAFRAME
        # =============================================

        df = pd.DataFrame([
            t.__dict__
            for t in transactions
        ])

        # =============================================
        # REMOVE INTERNAL SQLALCHEMY FIELDS
        # =============================================

        df.drop(
            columns=["_sa_instance_state"],
            inplace=True,
            errors="ignore"
        )

        # =============================================
        # SORT BY TIMESTAMP
        # =============================================

        if "timestamp" in df.columns:

            df = df.sort_values(
                "timestamp",
                ascending=False
            )

        # =============================================
        # EXPORT
        # =============================================

        output_file = "export_transactions.csv"

        df.to_csv(
            output_file,
            index=False
        )

        # =============================================
        # SUMMARY
        # =============================================

        total = len(df)

        fraud_count = (
            df["is_fraud"].sum()
            if "is_fraud" in df.columns
            else 0
        )

        print(
            f"\n✅ Database exported successfully"
        )

        print(
            f"📄 File: {output_file}"
        )

        print(
            f"📊 Transactions: {total}"
        )

        print(
            f"🚨 Fraud Transactions: {fraud_count}"
        )

    # ================================================
    # ERROR HANDLING
    # ================================================

    except Exception as e:

        print(
            "\n❌ Export failed"
        )

        print(
            "ERROR:",
            str(e)
        )

    finally:

        db.close()


# =====================================================
# ENTRYPOINT
# =====================================================

if __name__ == "__main__":

    export_transactions()