from backend.profile_builder import get_profile_status
def calculate_user_risk(user_df, suspicious_count=None, max_risk=None, fanout_flag=None):

    if user_df.empty:
        return {
            "risk_score": 0,
            "status": "NORMAL",
            "fraud_ratio": 0,
            "fraud_count": 0,
            "avg_risk": 0,
            "max_risk": round(
                max_risk,
                2
            ),
            "suspicious_count":
                suspicious_count,

            "fanout_flag":
                fanout_flag,
        }

    total_transactions = len(user_df)

    fraud_count = int(
        user_df["is_fraud"].sum()
    )

    fraud_ratio = (
        fraud_count / total_transactions
    )

    avg_risk = float(
        user_df["risk_score"].mean()
    )

    country_count = user_df[
        "country"
    ].nunique()

    device_count = user_df[
        "device"
    ].nunique()

    ip_count = user_df[
        "ip_address"
    ].nunique()

    # =====================================
    # FINAL USER RISK
    # =====================================

    risk_score = 0

    # AI average risk
    risk_score += avg_risk * 40

    # fraud ratio influence
    risk_score += fraud_ratio * 20

    # fraud history
    risk_score += min(
        fraud_count * 5,
        30
    )

    # geo anomaly
    if country_count >= 4:
        risk_score += 10

    # device anomaly
    if device_count >= 4:
        risk_score += 8

    # IP anomaly
    if ip_count >= 10:
        risk_score += 6

    risk_score = min(
        round(risk_score, 2),
        100
    )

    # =====================================
    # USER STATUS
    # =====================================

    # =====================================
    # USER STATUS
    # =====================================

    suspicious_count = len(

        user_df[

            user_df["risk_level"]

            .isin([

                "REVIEW",
                "DECLINED"
            ])

        ]
    )

    fanout_flag = False

    if "fraud_reasons" in user_df.columns:
        fanout_flag = (

            user_df["fraud_reasons"]

            .astype(str)

            .str.contains(
                "recipient_fan_out",
                na=False
            )

            .any()
        )

    hard_block_flag = False

    if "fraud_reasons" in user_df.columns:
        hard_block_flag = (

            user_df["fraud_reasons"]

            .astype(str)

            .str.contains(
                "amount_above_absolute_max|blacklisted_recipient|sanctioned_country",
                na=False
            )

            .any()
        )

    max_risk = float(
        user_df["risk_score"].max()
    )

    # =====================================
    # FINAL USER STATUS
    # =====================================

    recent_tx = user_df.sort_values(
        "timestamp"
    ).tail(20)

    recent_review_count = len(

        recent_tx[
            recent_tx["risk_level"] == "REVIEW"
            ]

    )

    recent_declined_count = len(

        recent_tx[
            recent_tx["risk_level"] == "DECLINED"
            ]

    )

    # =====================================
    # FINAL USER STATUS
    # =====================================

    profile_status = get_profile_status(
        total_transactions
    )

    # -------------------------------------
    # NEW / LEARNING USERS
    # -------------------------------------

    if profile_status != "ESTABLISHED":

        if (

                hard_block_flag

                or

                recent_declined_count >= 1

                or

                fraud_ratio > 0

        ):

            status = "WATCH"

        else:

            status = "NORMAL"

    # -------------------------------------
    # ESTABLISHED USERS
    # -------------------------------------

    else:

        if (

                hard_block_flag

                or

                recent_declined_count >= 2

                or

                (
                        fraud_ratio >= 0.15
                        and
                        avg_risk >= 0.25
                )

        ):

            status = "SUSPICIOUS"

        elif (

                recent_review_count >= 3

                or

                avg_risk >= 0.35

                or

                fraud_ratio >= 0.10

        ):

            status = "WATCH"

        else:

            status = "NORMAL"

    return {

        "risk_score": risk_score,

        "status": status,

        "fraud_ratio": round(
            fraud_ratio * 100,
            2
        ),

        "fraud_count": fraud_count,

        "avg_risk": round(
            avg_risk,
            3
        ),

        "country_count": country_count,

        "device_count": device_count,

        "ip_count": ip_count
    }