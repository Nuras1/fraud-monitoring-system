import pandas as pd
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.exc import IntegrityError

from backend.ai.risk_engine import calculate_risk
from backend.database import Base, engine, get_db
from backend.models import Transaction
from backend.schemas import (
    TransactionCreate,
    TransactionResponse
)
from fastapi import FastAPI
import pandas as pd
import os
from backend.user_risk_engine import calculate_user_risk

app = FastAPI(title="Fraud Monitoring System")


# =====================================================
# DB INIT
# =====================================================
@app.get("/transactions_csv")
def get_transactions_csv():

    csv_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "transactions.csv"
    )

    df = pd.read_csv(csv_path)

    # Заменяем все NaN
    df = df.fillna("")

    # Преобразуем DataFrame в обычные dict
    records = df.astype(object).to_dict(
        orient="records"
    )

    return records

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


# =====================================================
# CREATE TRANSACTION
# =====================================================

@app.post(
    "/transactions",
    response_model=TransactionResponse
)
def create_transaction(
    tx: TransactionCreate,
    db: Session = Depends(get_db)
):

    try:

        # =================================================
        # DUPLICATE CHECK
        # =================================================

        existing_tx = db.query(Transaction).filter(
            Transaction.transaction_id == tx.transaction_id
        ).first()

        if existing_tx:
            raise HTTPException(
                status_code=400,
                detail="Transaction already exists"
            )

        # =================================================
        # USER HISTORY
        # =================================================

        user_history = (
            db.query(Transaction)
            .filter(Transaction.user_id == tx.user_id)
            .order_by(Transaction.timestamp.desc())
            .limit(100)
            .all()
        )


        user_df = pd.DataFrame(
            [u.__dict__ for u in user_history]
        ) if user_history else pd.DataFrame()

        blocked_tx = (

            db.query(Transaction)

            .filter(
                Transaction.user_id == tx.user_id,
                Transaction.risk_level == "DECLINED"
            )

            .first()
        )

        if blocked_tx:
            raise HTTPException(
                status_code=403,
                detail="User account blocked"
            )
        # =================================================
        # BLOCKED USER CHECK
        # =================================================

        if user_history:

            user_df = pd.DataFrame(
                [u.__dict__ for u in user_history]
            )

            user_risk = calculate_user_risk(
                user_df
            )

            if user_risk["status"] == "SUSPICIOUS":
                raise HTTPException(
                    status_code=403,
                    detail="User account blocked"
                )
        # =================================================
        # RISK ANALYSIS
        # =================================================

        risk_score, reasons = calculate_risk(
            tx.dict(),
            user_df
        )

        # =================================================
        # RISK LEVELS
        # =================================================

        if risk_score >= 0.65:

            risk_level = "DECLINED"

        elif risk_score >= 0.40:

            risk_level = "REVIEW"

        else:

            risk_level = "APPROVED"

        is_fraud = risk_level != "APPROVED"

        # =================================================
        # SAVE TRANSACTION
        # =================================================

        db_tx = Transaction(
            transaction_id=tx.transaction_id,
            user_id=tx.user_id,

            amount=tx.amount,
            currency=tx.currency,
            country=tx.country,

            ip_address=tx.ip_address,
            device=tx.device,

            recipient_id=tx.recipient_id,
            recipient_country=tx.recipient_country,
            recipient_is_resident=tx.recipient_is_resident,
            sender_is_resident=tx.sender_is_resident,
            account_age_days=tx.account_age_days,

            timestamp=tx.timestamp,

            merchant=tx.merchant,
            payment_method=tx.payment_method,

            user_age=tx.user_age,
            user_registration_country=tx.user_registration_country,

            card_type=tx.card_type,
            transaction_type=tx.transaction_type,

            is_fraud=is_fraud,
            risk_score=float(risk_score),
            risk_level=risk_level,
            fraud_reasons=" | ".join(reasons)
        )

        db.add(db_tx)
        db.commit()
        db.refresh(db_tx)

        print(
            f"[RISK ENGINE] "
            f"TX={tx.transaction_id} "
            f"USER={tx.user_id} "
            f"SCORE={risk_score:.2f} "
            f"LEVEL={risk_level}"
        )

        # =================================================
        # RESPONSE
        # =================================================

        return {
            **tx.dict(),

            "is_fraud": is_fraud,
            "risk_score": round(float(risk_score), 3),
            "risk_level": risk_level,
            "reasons": reasons
        }

    # =====================================================
    # DUPLICATE / CONSTRAINT ERRORS
    # =====================================================

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Database integrity error"
        )

    # =====================================================
    # HTTP ERRORS
    # =====================================================

    except HTTPException:

        raise

    # =====================================================
    # GENERAL ERRORS
    # =====================================================

    except Exception as e:

        db.rollback()

        print("[ERROR]", str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =====================================================
# GET ALL TRANSACTIONS
# =====================================================

@app.get(
    "/transactions",
    response_model=List[TransactionResponse]
)
def get_transactions(
    db: Session = Depends(get_db)
):

    transactions = (
        db.query(Transaction)
        .order_by(Transaction.timestamp.desc())
        .all()
    )

    return transactions