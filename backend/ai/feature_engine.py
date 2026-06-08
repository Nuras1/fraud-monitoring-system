import pandas as pd
import numpy as np
import joblib

from sklearn.preprocessing import LabelEncoder


# =====================================================
# GLOBAL ENCODERS
# =====================================================

encoders = {}
try:
    encoders = joblib.load(
        "encoders.pkl"
    )
    print("✅ Encoders loaded")
except:
    print("⚠ Encoders not loaded")
# =====================================================
# CATEGORICAL FEATURES
# =====================================================

categorical_cols = [

    "currency",
    "country",

    "device",

    "merchant",

    "payment_method",

    "card_type",

    "transaction_type",

    "user_registration_country",

    "recipient_id",
    "recipient_country"
]


# =====================================================
# FEATURE ENGINEERING
# =====================================================

def preprocess(df, training=False):

    df = df.copy()

    # =================================================
    # TIMESTAMP FEATURES
    # =================================================

    if "timestamp" in df.columns:

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        df["hour"] = df["timestamp"].dt.hour

        df["day"] = df["timestamp"].dt.day

        df["day_of_week"] = (
            df["timestamp"].dt.dayofweek
        )

        df["is_weekend"] = (
            df["day_of_week"].isin([5, 6])
        ).astype(int)

        df["is_night"] = (
            df["hour"].isin([0, 1, 2, 3, 4])
        ).astype(int)

    # =================================================
    # AMOUNT FEATURES
    # =================================================

    if "amount" in df.columns:

        df["high_amount"] = (
            df["amount"] > 3000
        ).astype(int)

        df["very_high_amount"] = (
            df["amount"] > 7000
        ).astype(int)

        # log normalization
        df["amount_log"] = (
            df["amount"]
            .fillna(0)
            .apply(lambda x: max(x, 1))
            .apply(lambda x: np.log(x))
        )

    # =================================================
    # GEO FEATURES
    # =================================================

    if (
        "country" in df.columns
        and "user_registration_country" in df.columns
    ):

        df["country_mismatch"] = (
            df["country"]
            != df["user_registration_country"]
        ).astype(int)
    # =================================================
    # RECIPIENT FEATURES
    # =================================================

    if (
            "recipient_country" in df.columns
            and "country" in df.columns
    ):
        df["cross_border_transfer"] = (

                df["country"]

                !=

                df["recipient_country"]

        ).astype(int)

    if (
            "recipient_is_resident" in df.columns
            and "sender_is_resident" in df.columns
    ):
        df["resident_mismatch"] = (

                df["recipient_is_resident"]

                !=

                df["sender_is_resident"]

        ).astype(int)
    # =================================================
    # DEVICE FEATURES
    # =================================================

    if "device" in df.columns:

        suspicious_devices = [
            "Unknown",
            "Emulator",
            "VirtualMachine"
        ]

        df["suspicious_device"] = (
            df["device"]
            .isin(suspicious_devices)
        ).astype(int)
    # =================================================
    # BOOLEAN FEATURES
    # =================================================

    bool_cols = [

        "recipient_is_resident",

        "sender_is_resident"
    ]

    for col in bool_cols:

        if col in df.columns:
            df[col] = (

                df[col]

                .astype(str)

                .str.lower()

                .map({

                    "true": 1,
                    "false": 0

                })

                .fillna(0)
            )
            if "account_age_days" in df.columns:
                df["account_age_days"] = pd.to_numeric(

                    df["account_age_days"],

                    errors="coerce"

                ).fillna(0)
    # =================================================
    # FILL MISSING VALUES
    # =================================================

    df = df.fillna("unknown")

    # =================================================
    # ENCODE CATEGORICAL FEATURES
    # =================================================

    for col in categorical_cols:

        if col not in df.columns:
            continue

        # =============================================
        # TRAINING MODE
        # =============================================

        if training:

            enc = LabelEncoder()

            df[col] = enc.fit_transform(
                df[col].astype(str)
            )

            encoders[col] = enc

        # =============================================
        # INFERENCE MODE
        # =============================================

        else:

            enc = encoders.get(col)

            if enc:

                values = []

                for value in df[col].astype(str):

                    # unseen category
                    if value not in enc.classes_:
                        values.append(-1)

                    else:
                        values.append(
                            enc.transform([value])[0]
                        )

                df[col] = values

    # =================================================
    # DROP UNUSED COLUMNS
    # =================================================

    drop_cols = [
        "timestamp",
        "fraud_reasons",
        "_sa_instance_state",

        # identifiers
        "user_id",
        "transaction_id",
        "recipient_id",
        "ip_address",

        # system generated fields
        "risk_level",
        "risk_score"
    ]

    df = df.drop(
        columns=drop_cols,
        errors="ignore"
    )

    # =================================================
    # FINAL CLEANUP
    # =================================================

    df = df.fillna(0)

    return df