class RuleEngine:

    def __init__(self):

        self.abs_max_amount = 2000000

        self.sanctioned_countries = {

            "IR",
            "KP",
            "SY"
        }

        self.blacklisted_recipients = {

            "U9999",
            "U8888"
        }

    # ==========================================
    # HARD RULES
    # ==========================================

    def hard_checks(self, tx):

        reasons = []

        # RH1

        if tx["amount"] > self.abs_max_amount:

            reasons.append(
                "amount_above_absolute_max"
            )

        # RH2

        if tx.get(
            "recipient_id"
        ) in self.blacklisted_recipients:

            reasons.append(
                "blacklisted_recipient"
            )

        # RH3

        if (

            tx.get("country")
            in self.sanctioned_countries

            or

            tx.get("recipient_country")
            in self.sanctioned_countries

        ):

            reasons.append(
                "sanctioned_country"
            )

        return (

            len(reasons) > 0,

            reasons
        )