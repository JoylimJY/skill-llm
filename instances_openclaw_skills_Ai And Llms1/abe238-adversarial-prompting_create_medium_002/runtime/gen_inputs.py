import json
from pathlib import Path


def main():
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    (data_dir / "pricing_brief.txt").write_text(
        """MARKER_PRICING_BRIEF_V1

Company: Northstar Analytics
Product: B2B dashboard for small finance teams
Current plan: Free tier + paid Pro tier
Decision under review: keep free tier, move to 14-day trial, or launch usage-based entry plan
Constraints: small team, limited support bandwidth, churn sensitivity, need faster conversion signals
Known concern: free tier attracts hobby users and raises support load
""",
        encoding="utf-8",
    )

    payload = {
        "customer_segments": [
            {"name": "Solo founders", "pain": "high curiosity, low willingness to pay"},
            {"name": "Small finance teams", "pain": "need collaboration and exports"},
            {"name": "Agency analysts", "pain": "burst usage, seasonal demand"},
        ],
        "metrics": {
            "trial_to_paid": 0.18,
            "free_to_paid": 0.06,
            "support_tickets_per_100_users": 14,
        },
        "markers": ["MARKER_JSON_V1", "MARKER_SEGMENT_C"],
    }
    (data_dir / "market_signals.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    (data_dir / "notes.md").write_text(
        """# Internal Notes

MARKER_NOTES_V1
- Sales wants faster conversion.
- Support wants fewer low-intent accounts.
- Engineering can ship only one gating change this quarter.
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()