import numpy as np

from backend.ai.rule_engine import rule_engine
import pandas as pd
from backend.ai.ml_model import predict
from backend.ai.anomaly_model import anomaly_score
from backend.ai.behaviour_engine import user_behaviour_score
from backend.ai.explain_engine import combine_reasons
from backend.profile_builder import build_profile

# =====================================================
# RISK ENGINE
# =====================================================

def calculate_risk(tx_dict, user_df=None):

    # =================================================
    # ENGINE RESULTS
    # =================================================

    ml_prob = 0
    rule_val = 0
    anomaly_val = 0
    behaviour_val = 0

    rule_reason = []
    behaviour_reason = []

    # =================================================
    # MACHINE LEARNING MODEL
    # =================================================

    try:

        ml_prob = predict(tx_dict)

    except Exception as e:

        print(
            "[ML ENGINE ERROR]",
            str(e)
        )

    # =================================================
    # USER PROFILE
    # =================================================

    user_profile = None

    recent_user_txs = []

    if user_df is not None and not user_df.empty:
        user_profile = build_profile(
            user_df
        )

        recent_user_txs = (
            user_df.to_dict(
                orient="records"
            )
        )

    # =================================================
    # RULE ENGINE
    # =================================================

    try:

        rule_val, rule_reason = (

            rule_engine.evaluate(

                tx_dict,

                user_profile,

                recent_user_txs
            )
        )

    except Exception as e:

        print(
            "[RULE ENGINE ERROR]",
            str(e)
        )

    # =================================================
    # ANOMALY DETECTION
    # =================================================

    try:

        anomaly_val = anomaly_score(tx_dict)

    except Exception as e:

        print(
            "[ANOMALY ENGINE ERROR]",
            str(e)
        )

    # =================================================
    # USER BEHAVIOUR ENGINE
    # =================================================

    try:

        if (
            user_df is not None
            and not user_df.empty
        ):

            behaviour_val, behaviour_reason = (
                user_behaviour_score(
                    user_df,
                    tx_dict
                )
            )

    except Exception as e:

        print(
            "[BEHAVIOUR ENGINE ERROR]",
            str(e)
        )

    # =================================================
    # RISK AGGREGATION
    # =================================================

    final_score = np.clip(

        ml_prob * 0.25 +

        anomaly_val * 0.15 +

        behaviour_val * 0.10 +

        rule_val * 0.50,

        0,
        1
    )

    # =================================================
    # RISK ESCALATION
    # =================================================

    high_risk_indicators = 0

    if ml_prob >= 0.8:
        high_risk_indicators += 1

    if anomaly_val >= 0.7:
        high_risk_indicators += 1

    if behaviour_val >= 0.7:
        high_risk_indicators += 1

    if rule_val >= 0.7:
        high_risk_indicators += 1

    # multiple engines agree
    if high_risk_indicators >= 3:

        final_score = min(
            1.0,
            final_score + 0.15
        )

        rule_reason.append(
            "Multiple fraud engines triggered"
        )

    # =================================================
    # CRITICAL FRAUD PATTERNS
    # =================================================

    amount = float(
        tx_dict.get("amount", 0)
    )

    device = str(
        tx_dict.get("device", "")
    ).lower()

    country = tx_dict.get("country")
    registration_country = tx_dict.get(
        "user_registration_country"
    )

    # very suspicious combination
    if (
        amount > 7000
        and device == "unknown"
        and country != registration_country
    ):

        final_score = max(
            final_score,
            0.95
        )

        rule_reason.append(
            "Critical fraud pattern detected"
        )

    # =================================================
    # FINAL NORMALIZATION
    # =================================================

    final_score = round(
        float(
            np.clip(final_score, 0, 1)
        ),
        3
    )

    # =================================================
    # EXPLAINABILITY
    # =================================================

    reasons = combine_reasons(
        rule_reason,
        behaviour_reason
    )

    # =================================================
    # DEBUG LOGGING
    # =================================================

    print(
        f"[RISK ENGINE] "
        f"ML={ml_prob:.2f} "
        f"RULE={rule_val:.2f} "
        f"ANOMALY={anomaly_val:.2f} "
        f"BEHAVIOUR={behaviour_val:.2f} "
        f"FINAL={final_score:.2f}"
    )

    return final_score, reasons
# =====================================================
# USER INVESTIGATION ANALYSIS
# =====================================================

def analyze_user(user_df):

    alerts = []

    try:

        if user_df is None or user_df.empty:
            return ["No user history"]

        # =============================================
        # HIGH AMOUNT
        # =============================================

        if user_df["amount"].max() > 10000:

            alerts.append(
                "💰 High-value transactions detected"
            )

        # =============================================
        # MULTIPLE COUNTRIES
        # =============================================

        if user_df["country"].nunique() >= 4:

            alerts.append(
                "🌍 Multiple countries detected"
            )

        # =============================================
        # UNKNOWN DEVICES
        # =============================================

        suspicious_devices = [
            "unknown",
            "emulator",
            "virtualmachine"
        ]

        devices = (
            user_df["device"]
            .astype(str)
            .str.lower()
            .tolist()
        )

        if any(
            d in suspicious_devices
            for d in devices
        ):

            alerts.append(
                "📱 Suspicious device detected"
            )

        # =============================================
        # MULTIPLE IPS
        # =============================================

        if user_df["ip_address"].nunique() > 20:

            alerts.append(
                "🌐 Multiple IP addresses detected"
            )

        # =============================================
        # FRAUD RATIO
        # =============================================

        fraud_count = (
            user_df["is_fraud"]
            .sum()
        )

        total_count = len(user_df)

        if total_count > 0:

            fraud_ratio = (
                fraud_count / total_count
            )

            if fraud_ratio >= 0.4:

                alerts.append(
                    "🚨 High fraud ratio"
                )

        # =============================================
        # VELOCITY FRAUD
        # =============================================

        if total_count > 75:

            alerts.append(
                "⚡ High transaction frequency"
            )

        # =============================================
        # NIGHT ACTIVITY
        # =============================================

        if "timestamp" in user_df.columns:

            timestamps = pd.to_datetime(
                user_df["timestamp"],
                errors="coerce"
            )

            night_count = (

                timestamps.dt.hour
                .isin([0,1,2,3,4])
                .sum()
            )

            if night_count >= 3:

                alerts.append(
                    "🌙 Suspicious night activity"
                )

    except Exception as e:

        print(
            "[USER ANALYSIS ERROR]",
            str(e)
        )

    return alerts