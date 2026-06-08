import pandas as pd
import numpy as np

from backend.profile_builder import build_profile
from backend.rule_engine_v2 import RuleEngine
from backend.ai.rule_engine import rule_engine
from backend.ai.ml_model import predict
from backend.ai.anomaly_model import anomaly_score
from backend.ai.behaviour_engine import user_behaviour_score
from backend.ai.explain_engine import combine_reasons

new_rule_engine = RuleEngine()
# =====================================================
# RISK ENGINE
# =====================================================

def calculate_risk(tx_dict, user_df=None):

    # =================================================
    # DEFAULT VALUES
    # =================================================

    ml_prob = 0
    rule_val = 0
    anomaly_val = 0
    behaviour_val = 0

    rule_reason = []
    behaviour_reason = []

    # =================================================
    # USER PROFILE
    # =================================================

    profile = None

    if user_df is not None and not user_df.empty:

        profile = build_profile(
            user_df
        )

        recent_user_txs = (
            user_df.to_dict(
                orient="records"
            )
        )

    else:

        recent_user_txs = []
    # ==========================================
    # HARD RULES
    # ==========================================

    hard_block = False

    try:

        hard_block, hard_reasons = (

            new_rule_engine.hard_checks(
                tx_dict
            )
        )

    except Exception as e:

        print(
            "[HARD RULE ERROR]",
            str(e)
        )

        hard_reasons = []

    if hard_block:
        return {

            "risk_score": 1.0,

            "risk_level": "DECLINED",

            "rule_hard_block": True,

            "reasons": hard_reasons
        }
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
    # RULE ENGINE
    # =================================================

    try:

        rule_val, rule_reason = (
            rule_engine.evaluate(
                tx_dict,
                profile,
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
    # FINAL RISK AGGREGATION
    # =================================================

    final_score = np.clip(

        # ML model
        (ml_prob * 0.45)

        +

        # Rule engine
        (rule_val * 0.25)

        +

        # Anomaly detection
        (anomaly_val * 0.20)

        +

        # Behaviour analysis
        (behaviour_val * 0.10),

        0,
        1
    )

    # =================================================
    # MULTI-ENGINE ESCALATION
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
            "multiple_fraud_engines_triggered"
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

    tx_country = tx_dict.get("country")

    registration_country = tx_dict.get(
        "user_registration_country"
    )

    # extremely suspicious combination
    if (

        amount >= 7000

        and device == "unknown"

        and tx_country != registration_country
    ):

        final_score = max(
            final_score,
            0.95
        )

        rule_reason.append(
            "critical_fraud_pattern_detected"
        )

    # =================================================
    # NORMALIZATION
    # =================================================

    final_score = round(
        float(
            np.clip(
                final_score,
                0,
                1
            )
        ),
        3
    )

    # =================================================
    # RISK LEVEL
    # =================================================

    if final_score >= 0.85:

        risk_level = "BLOCKED"

    elif final_score >= 0.65:

        risk_level = "REVIEW"

    else:

        risk_level = "APPROVED"

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

    # =================================================
    # RETURN
    # =================================================

    return {
        "risk_score": final_score,
        "risk_level": risk_level,
        "reasons": reasons
    }


# =====================================================
# USER INVESTIGATION ENGINE
# =====================================================

def analyze_user(user_df):

    alerts = []

    if user_df is None or user_df.empty:
        return alerts

    # =================================================
    # HIGH RISK TRANSACTIONS
    # =================================================

    if "risk_score" in user_df.columns:

        high_risk = user_df[
            user_df["risk_score"] >= 0.8
        ]

        if len(high_risk) >= 3:

            alerts.append(
                f"🚨 {len(high_risk)} high-risk transactions detected"
            )

    # =================================================
    # FRAUD COUNT
    # =================================================

    if "is_fraud" in user_df.columns:

        fraud_count = (
            user_df["is_fraud"] == True
        ).sum()

        if fraud_count >= 3:

            alerts.append(
                "⚠ Multiple fraud transactions detected"
            )

    # =================================================
    # COUNTRY ANALYSIS
    # =================================================

    if "country" in user_df.columns:

        unique_countries = (
            user_df["country"]
            .nunique()
        )

        if unique_countries >= 4:

            alerts.append(
                "🌍 Multiple countries detected"
            )

    # =================================================
    # DEVICE ANALYSIS
    # =================================================

    if "device" in user_df.columns:

        if (
            user_df["device"]
            .astype(str)
            .str.lower()
            .isin(["unknown", "emulator"])
            .any()
        ):

            alerts.append(
                "📱 Suspicious device activity"
            )

    # =================================================
    # IP ANALYSIS
    # =================================================

    if "ip_address" in user_df.columns:

        unique_ips = (
            user_df["ip_address"]
            .nunique()
        )

        if unique_ips >= 10:

            alerts.append(
                "🌐 Multiple IP addresses detected"
            )

    # =================================================
    # VELOCITY FRAUD
    # =================================================

    if (
        "timestamp" in user_df.columns
        and len(user_df) >= 5
    ):

        try:

            timestamps = pd.to_datetime(
                user_df["timestamp"],
                errors="coerce"
            )

            latest = timestamps.max()

            recent = timestamps[
                timestamps >= latest - pd.Timedelta(minutes=10)
            ]

            if len(recent) >= 5:

                alerts.append(
                    "⚡ High transaction velocity detected"
                )

        except:
            pass

    # =================================================
    # FRAUD REASONS
    # =================================================

    if "fraud_reasons" in user_df.columns:

        reasons = []

        for value in user_df[
            "fraud_reasons"
        ].dropna():

            parts = str(value).split("|")

            reasons.extend(parts)

        if reasons:

            top_reasons = (
                pd.Series(reasons)
                .value_counts()
                .head(2)
                .index
                .tolist()
            )

            for reason in top_reasons:

                alerts.append(
                    f"🧠 Frequent fraud indicator: {reason}"
                )

    return alerts