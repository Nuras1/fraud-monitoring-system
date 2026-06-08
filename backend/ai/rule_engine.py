from datetime import datetime


# =====================================================
# RULE ENGINE CONFIG
# =====================================================

RULE_CONFIG = {

    "amount_limit": 5000,

    "abs_max_amount": 2000000,

    "new_user_amount_limit": 5000,

    "night_start": 23,
    "night_end": 6,

    "velocity_window_min": 10,

    "velocity_max_count": 5,

    "new_user_velocity_max": 3,

    "velocity_factor": 3.0,

    "fanout_max": 6,

    "profile_min_tx": 10,

    "home_country": "KZ",

    "high_risk_countries": [
        "IR",
        "KP"
    ],

    "sanctioned_countries": [
        "IR",
        "KP",
        "SY"
    ],

    "blacklisted_recipients": [

        "U9999",
        "U8888"
    ],

    "suspicious_ip_ranges": [
        "185.",
        "172."
    ]
}


# =====================================================
# RULE-BASED FRAUD ENGINE
# =====================================================

class RuleEngine:

    def __init__(self, config):

        self.amount_limit = config[
            "amount_limit"
        ]
        self.abs_max_amount = config[
            "abs_max_amount"
        ]

        self.new_user_amount_limit = config[
            "new_user_amount_limit"
        ]

        self.new_user_velocity_max = config[
            "new_user_velocity_max"
        ]

        self.velocity_factor = config[
            "velocity_factor"
        ]

        self.fanout_max = config[
            "fanout_max"
        ]

        self.profile_min_tx = config[
            "profile_min_tx"
        ]

        self.home_country = config[
            "home_country"
        ]

        self.sanctioned_countries = set(
            config["sanctioned_countries"]
        )

        self.blacklisted_recipients = set(
            config["blacklisted_recipients"]
        )
        self.night_start = config[
            "night_start"
        ]

        self.night_end = config[
            "night_end"
        ]

        self.velocity_window_min = config[
            "velocity_window_min"
        ]

        self.velocity_max_count = config[
            "velocity_max_count"
        ]

        self.high_risk_countries = config[
            "high_risk_countries"
        ]

        self.suspicious_ip_ranges = config[
            "suspicious_ip_ranges"
        ]

    # =================================================
    # AMOUNT ANALYSIS
    # =================================================

    def check_amount(
            self,
            tx,
            user_profile
    ):

        score = 0.0
        reason = None

        amount = float(
            tx.get("amount", 0)
        )

        mean_amount = user_profile.get(
            "mean_amount",
            0
        )

        std_amount = user_profile.get(
            "std_amount",
            0
        )

        p95_amount = user_profile.get(
            "p95_amount",
            0
        )

        # ==========================================
        # RP1A
        # ==========================================

        if (

                amount > mean_amount + (3 * std_amount)

                or

                (
                        p95_amount > 0
                        and
                        amount > p95_amount * 2
                )

        ):

            score = 0.40

            reason = (
                "amount_far_above_baseline"
            )

        # ==========================================
        # RP1B
        # ==========================================

        elif amount > mean_amount + (2 * std_amount):

            score = 0.20

            reason = (
                "amount_above_baseline"
            )

        return score, reason

    # =================================================
    # GEOGRAPHY ANALYSIS
    # =================================================

    def check_geography(
        self,
        tx,
        user_profile
    ):

        score = 0.0
        reason = None

        tx_country = tx.get("country")

        registration_country = tx.get(
            "user_registration_country"
        )

        typical_countries = user_profile.get(
            "typical_countries",
            []
        )

        # high risk country
        if tx_country in self.high_risk_countries:

            score = 0.35

            reason = (
                "high_risk_country"
            )

        # new country for user
        elif (
            tx_country
            and tx_country not in typical_countries
        ):

            score = 0.15

            reason = (
                "new_country_for_user"
            )

        # mismatch with registration
        elif (
            tx_country
            and registration_country
            and tx_country != registration_country
        ):

            score = 0.15

            reason = (
                "country_differs_from_registration"
            )

        return score, reason

    # =================================================
    # DEVICE + IP ANALYSIS
    # =================================================

    def check_device(
        self,
        tx,
        user_profile
    ):

        score = 0.0
        reason = None

        device = tx.get("device")

        known_devices = user_profile.get(
            "known_devices",
            []
        )

        # unknown device
        if str(device).lower() in [
            "unknown",
            "virtualmachine",
            "emulator"
        ]:
            score = 0.60
            reason = "high_risk_device"

        # suspicious IP
        ip_address = tx.get("ip_address")

        if (
            ip_address
            and self._is_suspicious_ip(
                ip_address
            )
        ):

            score += 0.15

            if reason:

                reason = (
                    reason
                    + "; suspicious_ip"
                )

            else:

                reason = "suspicious_ip"

        return min(score, 0.60), reason

    # =================================================
    # TIME ANALYSIS
    # =================================================

    def check_time_pattern(self, tx):

        score = 0.0
        reason = None

        timestamp = tx.get("timestamp")

        if not timestamp:
            return score, reason

        try:

            # string support
            if isinstance(timestamp, str):

                timestamp = datetime.fromisoformat(
                    timestamp
                )

            hour = timestamp.hour

            if (
                hour < self.night_end
                or hour >= self.night_start
            ):

                score = 0.10

                reason = "unusual_time"

        except:
            pass

        return score, reason

    # =================================================
    # VELOCITY FRAUD
    # =================================================

    def check_velocity(
            self,
            tx,
            recent_user_txs,
            user_profile
    ):

        score = 0.0
        reason = None

        timestamp = tx.get(
            "timestamp"
        )

        if not timestamp:
            return score, reason

        try:

            if isinstance(
                    timestamp,
                    str
            ):
                timestamp = (
                    datetime.fromisoformat(
                        timestamp
                    )
                )

            recent_count = 0

            for t in recent_user_txs:

                tx_time = t.get(
                    "timestamp"
                )

                if not tx_time:
                    continue

                if isinstance(
                        tx_time,
                        str
                ):
                    tx_time = (
                        datetime.fromisoformat(
                            tx_time
                        )
                    )

                delta = (

                        timestamp
                        - tx_time

                ).total_seconds()

                if (

                        delta
                        <=
                        self.velocity_window_min * 60

                ):
                    recent_count += 1

            avg_daily_tx = user_profile.get(
                "avg_daily_tx",
                1
            )

            threshold = (

                    avg_daily_tx
                    *
                    self.velocity_factor

            )

            if recent_count > threshold:
                score = 0.40

                reason = (
                    "velocity_above_baseline"
                )

        except:

            pass

        return score, reason

    # =================================================
    # PAYMENT METHOD ANALYSIS
    # =================================================

    def check_payment_method(
        self,
        tx,
        user_profile
    ):

        score = 0.0
        reason = None

        payment_method = tx.get(
            "payment_method"
        )

        typical_methods = user_profile.get(
            "typical_methods",
            []
        )

        if (
            payment_method
            and payment_method
            not in typical_methods
        ):

            score = 0.10

            reason = (
                "atypical_payment_method"
            )

        return score, reason

    # =================================================
    # IP CHECK
    # =================================================

    def _is_suspicious_ip(self, ip):

        return any(
            ip.startswith(prefix)
            for prefix
            in self.suspicious_ip_ranges
        )

    # =================================================
    # PROFILE MATURITY
    # =================================================

    def _is_established(
            self,
            user_profile
    ):

        if not user_profile:
            return False

        return (

                user_profile.get(
                    "tx_count",
                    0
                )

                >=

                self.profile_min_tx
        )

    # =================================================
    # TIER 1 - NEW USER RULES
    # =================================================

    def _new_user_checks(
            self,
            tx,
            recent_user_txs
    ):

        score = 0.05

        reasons = [
            "limited_history"
        ]

        amount = float(
            tx.get("amount", 0)
        )

        # RN1

        if amount > self.new_user_amount_limit:
            score += 0.30

            reasons.append(
                "new_user_high_amount"
            )

        # RN2

        if (
                tx.get("country")
                !=
                tx.get("user_registration_country")
        ):
            score += 0.25

            reasons.append(
                "new_user_foreign_transfer"
            )

        # RN3

        recent_count = 0

        timestamp = tx.get(
            "timestamp"
        )

        if timestamp:

            for t in recent_user_txs:

                tx_time = t.get(
                    "timestamp"
                )

                if not tx_time:
                    continue

                try:

                    delta = (
                            timestamp - tx_time
                    ).total_seconds()

                    if (
                            delta
                            <= self.velocity_window_min * 60
                    ):
                        recent_count += 1

                except:
                    pass

        if (
                recent_count
                >=
                self.new_user_velocity_max
        ):
            score += 0.30

            reasons.append(
                "new_user_high_velocity"
            )

        # RN4

        if not tx.get(
                "recipient_is_resident",
                True
        ):
            score += 0.20

            reasons.append(
                "new_user_nonresident_recipient"
            )

        # RN5

        hour = tx[
            "timestamp"
        ].hour

        if (
                hour < self.night_end
                or
                hour >= self.night_start
        ):
            score += 0.15

            reasons.append(
                "new_user_night_time"
            )

        return min(
            score,
            1.0
        ), reasons

    # =================================================
    # RP2 NEW RECIPIENT
    # =================================================

    def check_recipient(
            self,
            tx,
            user_profile
    ):

        score = 0.0
        reason = None

        recipient = tx.get(
            "recipient_id"
        )

        known_recipients = (

            user_profile.get(
                "known_recipients",
                set()
            )
        )

        if (

                recipient
                and

                recipient
                not in known_recipients

        ):
            score = 0.20

            reason = (
                "new_recipient"
            )

        return score, reason

    # =================================================
    # RP3 ATYPICAL HOUR
    # =================================================

    def check_typical_hour(
            self,
            tx,
            user_profile
    ):

        score = 0.0
        reason = None

        timestamp = tx.get(
            "timestamp"
        )

        if not timestamp:
            return score, reason

        try:

            if isinstance(
                    timestamp,
                    str
            ):
                timestamp = (
                    datetime.fromisoformat(
                        timestamp
                    )
                )

            hour = timestamp.hour

            typical_hours = (

                user_profile.get(
                    "typical_hours",
                    set()
                )
            )

            if (

                    typical_hours

                    and

                    hour
                    not in typical_hours

            ):
                score = 0.15

                reason = (
                    "atypical_hour_for_user"
                )

        except:

            pass

        return score, reason

    # =================================================
    # RP7 FAN OUT
    # =================================================

    def check_fanout(
            self,
            tx,
            recent_user_txs
    ):

        score = 0.0
        reason = None

        timestamp = tx.get(
            "timestamp"
        )

        if not timestamp:
            return score, reason

        try:

            if isinstance(
                    timestamp,
                    str
            ):
                timestamp = (
                    datetime.fromisoformat(
                        timestamp
                    )
                )

            recipients = set()

            for t in recent_user_txs:

                tx_time = t.get(
                    "timestamp"
                )

                if not tx_time:
                    continue

                if isinstance(
                        tx_time,
                        str
                ):
                    tx_time = (
                        datetime.fromisoformat(
                            tx_time
                        )
                    )

                delta = (

                        timestamp
                        - tx_time

                ).total_seconds()

                if (

                        delta
                        <=
                        self.velocity_window_min * 60

                ):

                    recipient = t.get(
                        "recipient_id"
                    )

                    if recipient:
                        recipients.add(
                            recipient
                        )

            if (

                    len(recipients)
                    >=
                    self.fanout_max

            ):
                score = 0.40

                reason = (
                    "recipient_fan_out"
                )

        except:

            pass

        return score, reason

    # =================================================
    # RG2 + RG3
    # =================================================

    def check_residency(
            self,
            tx
    ):

        score = 0.0

        reasons = []

        country = tx.get(
            "country"
        )

        recipient_country = tx.get(
            "recipient_country"
        )

        sender_is_resident = tx.get(
            "sender_is_resident",
            True
        )

        recipient_is_resident = tx.get(
            "recipient_is_resident",
            True
        )

        # ==========================================
        # RG2
        # ==========================================

        if (

                country
                and

                recipient_country
                and

                country != recipient_country

        ):
            score += 0.15

            reasons.append(
                "cross_border_transfer"
            )

        # ==========================================
        # RG3
        # ==========================================

        if (

                sender_is_resident
                !=
                recipient_is_resident

        ):
            score += 0.15

            reasons.append(
                "resident_nonresident_mismatch"
            )

        return score, reasons
    # =================================================
    # MAIN EVALUATION
    # =================================================

    def evaluate(
            self,
            tx,
            user_profile,
            recent_user_txs
    ):
        #blocked, hard_reasons = self.hard_checks(tx)

        #if blocked:
        #    return 1.0, hard_reasons
        # ==========================================
        # PROFILE STATUS
        # ==========================================

        if self._is_established(user_profile):

            profile_status = "ESTABLISHED"

        else:

            profile_status = "LEARNING"

        # ==========================================
        # TIER SELECTION
        # ==========================================

        if profile_status == "LEARNING":

            tier_score, tier_reasons = (

                self._new_user_checks(
                    tx,
                    recent_user_txs
                )
            )

            checks = []

        else:

            tier_score = 0
            tier_reasons = []

            checks = [

                self.check_amount(
                    tx,
                    user_profile
                ),
                self.check_recipient(
                    tx,
                    user_profile
                ),

                self.check_typical_hour(
                    tx,
                    user_profile
                ),

                self.check_geography(
                    tx,
                    user_profile
                ),

                self.check_device(
                    tx,
                    user_profile
                ),

                self.check_time_pattern(
                    tx
                ),

                self.check_velocity(
                    tx,
                    recent_user_txs,
                    user_profile
                ),
                self.check_fanout(
                    tx,
                    recent_user_txs
                ),
                self.check_payment_method(
                    tx,
                    user_profile
                )
            ]

        # ==========================================
        # SCORE AGGREGATION
        # ==========================================

        total_score = tier_score

        reasons = tier_reasons.copy()
        # ==========================================
        # SHARED RULES
        # ==========================================

        shared_score, shared_reasons = (

            self.check_residency(tx)

        )

        total_score += shared_score

        reasons.extend(
            shared_reasons
        )
        for score, reason in checks:

            total_score += score

            if reason:
                reasons.append(reason)

        total_score = min(
            total_score,
            1.0
        )

        reasons = list(
            dict.fromkeys(reasons)
        )

        reasons.append(
            f"profile_{profile_status}"
        )
        print(
            f"[RULE] SCORE={round(total_score, 3)} "
            f"REASONS={reasons}"
        )
        return round(total_score, 3), reasons

# =====================================================
# GLOBAL ENGINE INSTANCE
# =====================================================

rule_engine = RuleEngine(
    RULE_CONFIG
)