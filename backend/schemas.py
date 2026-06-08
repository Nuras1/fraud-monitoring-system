from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


# =====================================================
# BASE TRANSACTION
# =====================================================

class TransactionBase(BaseModel):

    transaction_id: str
    user_id: str

    amount: float = Field(gt=0)

    currency: str
    country: str

    ip_address: str
    device: str

    timestamp: Optional[datetime] = None

    merchant: Optional[str] = None
    payment_method: Optional[str] = None

    user_age: Optional[int] = Field(
        default=None,
        ge=18,
        le=100
    )

    user_registration_country: Optional[str] = None

    card_type: Optional[str] = None
    transaction_type: Optional[str] = None

    # =====================================================
    # P2P FIELDS
    # =====================================================

    recipient_id: Optional[str] = None

    recipient_country: Optional[str] = None

    recipient_is_resident: Optional[bool] = None

    sender_is_resident: Optional[bool] = None

    account_age_days: Optional[int] = 0


# =====================================================
# CREATE REQUEST
# =====================================================

class TransactionCreate(TransactionBase):
    pass


# =====================================================
# RESPONSE
# =====================================================

class TransactionResponse(TransactionBase):

    is_fraud: bool

    risk_score: float

    risk_level: str

    fraud_reasons: Optional[str] = None

    class Config:
        from_attributes = True