from collections import Counter
import numpy as np
import pandas as pd

MIN_TX = 10


def get_profile_status(tx_count):

    if tx_count == 0:
        return "NEW"

    if tx_count < MIN_TX:
        return "LEARNING"

    return "ESTABLISHED"

# =================================================
# AVG DAILY TX
# =================================================

def calculate_avg_daily_tx(user_df):

    if user_df.empty:
        return 0

    if "timestamp" not in user_df.columns:
        return 0

    dates = (

        user_df["timestamp"]

        .dropna()

        .dt.date

        .unique()
    )

    days = max(
        len(dates),
        1
    )

    return round(
        len(user_df) / days,
        2
    )
def build_profile(user_df):

    if user_df.empty:

        return None

    amounts = user_df["amount"].tolist()

    countries = user_df["country"].tolist()

    devices = user_df["device"].tolist()

    methods = user_df["payment_method"].tolist()

    recipients = []

    if "recipient_id" in user_df.columns:

        recipients = (
            user_df["recipient_id"]
            .dropna()
            .tolist()
        )

    hours = []

    if "timestamp" in user_df.columns:

        hours = (

            user_df["timestamp"]

            .dropna()

            .dt.hour

            .tolist()
        )

    profile = {

        "tx_count":
            len(user_df),

        "profile_status":
            get_profile_status(
                len(user_df)
            ),

        "mean_amount":
            float(np.mean(amounts)),

        "std_amount":
            float(np.std(amounts))
            if len(amounts) > 1
            else 0.0,

        "median_amount":
            float(np.median(amounts)),

        "max_amount":
            float(np.max(amounts)),

        "p95_amount":
            float(np.percentile(
                amounts,
                95
            )),

        "typical_countries":
            set(

                c

                for c, _ in Counter(
                    countries
                ).most_common(3)
            ),

        "known_devices":
            set(devices),

        "typical_methods":
            set(

                m

                for m, _ in Counter(
                    methods
                ).most_common(2)
            ),

        "known_recipients":
            set(recipients),

        "avg_daily_tx":
            calculate_avg_daily_tx(
                user_df
            ),
        "typical_hours":
            set(

                h

                for h, _ in Counter(
                    hours
                ).most_common(8)
            )
    }

    return profile