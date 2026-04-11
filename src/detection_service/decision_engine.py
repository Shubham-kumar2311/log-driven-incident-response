class DecisionEngine:
    """Combines rule, z-score, and ML outputs into one final hybrid decision."""

    @staticmethod
    def combine(
        rule_signals: list[dict],
        zscore_result: dict | None = None,
        ml_result: dict | None = None,
    ) -> dict:
        rule_triggered = len(rule_signals) > 0
        zscore_result = zscore_result or {}
        ml_result = ml_result or {}

        zscore_triggered = bool(zscore_result.get("is_anomaly", False))
        ml_triggered = bool(ml_result.get("is_anomaly", False))

        if rule_triggered and (zscore_triggered or ml_triggered):
            severity = "CRITICAL"
            source = "combined"
        elif zscore_triggered and ml_triggered:
            severity = "HIGH"
            source = "combined"
        elif rule_triggered:
            severity = "HIGH"
            source = "rule"
        elif zscore_triggered:
            severity = "MEDIUM"
            source = "zscore"
        elif ml_triggered:
            severity = "MEDIUM"
            source = "ml"
        else:
            severity = "NORMAL"
            source = "none"

        sources = []
        if rule_triggered:
            sources.append("rule")
        if zscore_triggered:
            sources.append("zscore")
        if ml_triggered:
            sources.append("ml")

        rule_type = None
        if rule_triggered:
            rule_type = ",".join(
                sorted({s.get("signal_type", s.get("rule_id", "unknown_rule")) for s in rule_signals})
            )

        return {
            "rule_triggered": rule_triggered,
            "zscore_triggered": zscore_triggered,
            "ml_triggered": ml_triggered,
            "severity": severity,
            "source": source,
            "detection_source": "+".join(sources) if sources else "none",
            "anomaly_score": ml_result.get("anomaly_score"),
            "z_score": zscore_result.get("z_score"),
            "z_score_request_rate": zscore_result.get("z_score_request_rate"),
            "z_score_error_ratio": zscore_result.get("z_score_error_ratio"),
            "rule_type": rule_type,
            "ml_used": bool(ml_result.get("ml_used", False)),
            "ml_error": ml_result.get("error"),
        }
