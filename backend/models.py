from sqlalchemy import (
    Column,
    String,
    Float,
    Boolean,
    Integer,
    DateTime,
    Text
)

from backend.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    # =====================================================
    # PRIMARY DATA
    # =====================================================

    id = Column(Integer, primary_key=True, index=True)

    transaction_id = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    user_id = Column(
        String,
        index=True,
        nullable=False
    )

    # =====================================================
    # TRANSACTION INFO
    # =====================================================

    amount = Column(Float, nullable=False)

    currency = Column(String)
    country = Column(String)

    ip_address = Column(String)
    device = Column(String)

    timestamp = Column(DateTime)

    merchant = Column(String)

    payment_method = Column(String)

    # =====================================================
    # USER INFO
    # =====================================================

    user_age = Column(Integer)

    user_registration_country = Column(String)

    card_type = Column(String)

    transaction_type = Column(String)

    # =====================================================
    # P2P FIELDS
    # =====================================================

    recipient_id = Column(String)

    recipient_country = Column(String)

    recipient_is_resident = Column(Boolean)

    sender_is_resident = Column(Boolean)

    account_age_days = Column(Integer, default=0)

    # =====================================================
    # FRAUD ANALYSIS
    # =====================================================

    is_fraud = Column(
        Boolean,
        default=False
    )

    # final risk score from AI engines
    risk_score = Column(
        Float,
        default=0
    )

    # APPROVED / REVIEW / BLOCKED
    risk_level = Column(
        String,
        default="APPROVED"
    )

    # explainability
    fraud_reasons = Column(
        Text,
        default=""
    )