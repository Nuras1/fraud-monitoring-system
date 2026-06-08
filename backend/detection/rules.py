# =====================================================
# RULE-BASED FRAUD DETECTION ENGINE
# =====================================================

def rule_based_detection(tx: dict):

    score = 0
    reasons = []

    # =================================================
    # HIGH AMOUNT
    # =================================================

    amount = float(tx.get("amount", 0))

    if amount > 5000:
        score += 0.4
        reasons.append(
            "High transaction amount"
        )

    elif amount > 3000:
        score += 0.2
        reasons.append(
            "Moderately high transaction amount"
        )

    # =================================================
    # GEO MISMATCH
    # =================================================

    tx_country = tx.get("country")
    registration_country = tx.get(
        "user_registration_country"
    )

    if (
        tx_country
        and registration_country
        and tx_country != registration_country
    ):

        score += 0.25

        reasons.append(
            "Transaction from different country"
        )

    # =================================================
    # UNKNOWN DEVICE
    # =================================================

    device = str(
        tx.get("device", "")
    ).lower()

    suspicious_devices = [
        "unknown",
        "emulator",
        "virtual_machine"
    ]

    if device in suspicious_devices:

        score += 0.3

        reasons.append(
            "Suspicious device detected"
        )

    # =================================================
    # SUSPICIOUS PAYMENT METHOD
    # =================================================

    payment_method = str(
        tx.get("payment_method", "")
    ).lower()

    if payment_method == "crypto":

        score += 0.15

        reasons.append(
            "High-risk payment method"
        )

    # =================================================
    # NIGHT ACTIVITY
    # =================================================

    timestamp = tx.get("timestamp")

    if timestamp:

        try:

            hour = timestamp.hour

            if hour in [0, 1, 2, 3, 4]:

                score += 0.15

                reasons.append(
                    "Night-time transaction activity"
                )

        except:
            pass

    # =================================================
    # FINAL RESULT
    # =================================================

    score = min(score, 1.0)

    is_fraud = score >= 0.65

    return {
        "is_fraud": is_fraud,
        "score": round(score, 3),
        "reasons": reasons
    }