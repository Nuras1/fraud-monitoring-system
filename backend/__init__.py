"""
AI package initialization
Fraud Monitoring System
"""

from backend.ai.risk_engine import calculate_risk
from backend.ai.behaviour_engine import user_behaviour_score
from backend.ai.anomaly_model import anomaly_score
from backend.ai.explain_engine import combine_reasons
from backend.ai.ml_model import predict


# =====================================================
# AI STATUS CHECK
# =====================================================

def ai():

    return {
        "status": "active",
        "engines": [
            "rule_engine",
            "ml_model",
            "anomaly_detection",
            "behaviour_analysis",
            "explainability"
        ]
    }


# =====================================================
# VERSION
# =====================================================

__version__ = "1.0.0"