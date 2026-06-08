import numpy as np

from collections import Counter


# =====================================================
# BEHAVIORAL ANALYZER
# =====================================================

class BehavioralAnalyzer:

    def __init__(
        self,
        history_window_days=30
    ):

        self.history_window_days = (
            history_window_days
        )

    # =================================================
    # BUILD USER PROFILE
    # =================================================

    def build_profile(
        self,
        user_transactions
    ):

        if not user_transactions:
            return None

        amounts = [

            t["amount"]

            for t in user_transactions

            if t.get("amount") is not None
        ]

        countries = [

            t["country"]

            for t in user_transactions

            if t.get("country")
        ]

        devices = [

            t["device"]

            for t in user_transactions

            if t.get("device")
        ]

        methods = [

            t["payment_method"]

            for t in user_transactions

            if t.get("payment_method")
        ]

        return {

            # =========================================
            # AMOUNT STATISTICS
            # =========================================

            "mean_amount":

                float(
                    np.mean(amounts)
                ),

            "std_amount":

                float(
                    np.std(amounts)
                )

                if len(amounts) > 1

                else 0.0,

            "median_amount":

                float(
                    np.median(amounts)
                ),

            # =========================================
            # USER ACTIVITY
            # =========================================

            "tx_count":

                len(user_transactions),

            # =========================================
            # GEO PROFILE
            # =========================================

            "typical_countries":

                set(

                    c

                    for c, _

                    in Counter(countries)
                    .most_common(3)
                ),

            # =========================================
            # DEVICE PROFILE
            # =========================================

            "known_devices":

                set(devices),

            # =========================================
            # PAYMENT PROFILE
            # =========================================

            "typical_methods":

                set(

                    m

                    for m, _

                    in Counter(methods)
                    .most_common(2)
                )
        }

    def evaluate(
            self,
            tx,
            user_profile
    ):

        if (

                user_profile is None

                or

                user_profile["tx_count"] < 5
        ):
            return 0.0, [
                "insufficient_history"
            ]

        score = 0.0

        reasons = []

        # =============================================
        # AMOUNT DEVIATION
        # =============================================

        amount_dev = self._amount_deviation(

            tx["amount"],

            user_profile
        )

        if amount_dev > 3:

            score += 0.40

            reasons.append(
                f"amount_deviation_{amount_dev:.1f}_sigma"
            )

        elif amount_dev > 2:

            score += 0.20

            reasons.append(
                "moderate_amount_deviation"
            )

        # =============================================
        # NEW COUNTRY
        # =============================================

        country = tx.get("country")

        if (

                country

                and

                country not in user_profile["typical_countries"]

        ):
            score += 0.15

            reasons.append(
                "new_country"
            )

        # =============================================
        # NEW DEVICE
        # =============================================

        device = tx.get("device")

        if (

                device

                and

                device not in user_profile["known_devices"]

        ):
            score += 0.15

            reasons.append(
                "new_device"
            )

        # =============================================
        # NEW PAYMENT METHOD
        # =============================================

        payment_method = tx.get(
            "payment_method"
        )

        if (

                payment_method

                and

                payment_method
                not in user_profile["typical_methods"]

        ):
            score += 0.10

            reasons.append(
                "new_payment_method"
            )
        # =============================================
        # USER SPENDING PATTERN
        # =============================================

        median_amount = user_profile.get(
            "median_amount",
            0
        )

        if (

                median_amount > 0

                and

                tx["amount"] > median_amount * 5

        ):
            score += 0.15

            reasons.append(
                "amount_above_user_pattern"
            )
        return min(score, 1.0), reasons

    # =================================================
    # AMOUNT DEVIATION
    # =================================================

    def _amount_deviation(
        self,
        amount,
        profile
    ):

        if profile["std_amount"] == 0:
            return 0.0

        return abs(

            amount
            -
            profile["mean_amount"]

        ) / profile["std_amount"]


# =====================================================
# GLOBAL ANALYZER
# =====================================================

behavioral_analyzer = BehavioralAnalyzer()


# =====================================================
# LEGACY COMPATIBILITY FUNCTION
# =====================================================

def user_behaviour_score(
    user_df,
    tx
):

    try:

        if (
            user_df is None
            or user_df.empty
        ):

            return 0.0, [
                "no_user_history"
            ]

        transactions = user_df.to_dict(
            orient="records"
        )

        profile = (
            behavioral_analyzer
            .build_profile(
                transactions
            )
        )

        return (
            behavioral_analyzer
            .evaluate(
                tx,
                profile
            )
        )

    except Exception as e:

        print(
            "[BEHAVIOUR ERROR]",
            str(e)
        )

        return 0.0, []