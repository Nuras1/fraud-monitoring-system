# =====================================================
# EXPLAINABILITY ENGINE
# =====================================================

def combine_reasons(*reason_lists):

    reasons = []

    # =================================================
    # MERGE ALL REASONS
    # =================================================

    for lst in reason_lists:

        if not lst:
            continue

        for reason in lst:

            if (
                reason
                and isinstance(reason, str)
            ):

                reasons.append(
                    reason.strip()
                )

    # =================================================
    # REMOVE DUPLICATES
    # =================================================

    unique_reasons = list(
        dict.fromkeys(reasons)
    )

    # =================================================
    # LIMIT SIZE
    # =================================================

    unique_reasons = unique_reasons[:10]

    # =================================================
    # DEFAULT MESSAGE
    # =================================================

    if not unique_reasons:

        unique_reasons = [
            "No suspicious indicators detected"
        ]

    return unique_reasons