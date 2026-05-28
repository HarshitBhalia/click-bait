from __future__ import annotations

from collections import Counter


def summarize_rows(rows: list[dict]) -> dict:
    label_distribution = Counter(str(row["label"]) for row in rows if row.get("label") in (0, 1, "0", "1"))
    category_distribution = Counter(str(row.get("channel_category", "")).strip() for row in rows if row.get("channel_category"))
    label_status_distribution = Counter(str(row.get("label_status", "")).strip() for row in rows if row.get("label_status"))
    transcript_language_distribution = Counter(
        str(row.get("transcript_language", "")).strip() for row in rows if row.get("transcript_language")
    )
    return {
        "total": len(rows),
        "label_distribution": dict(sorted(label_distribution.items())),
        "category_distribution": dict(category_distribution.most_common()),
        "label_status_distribution": dict(label_status_distribution.most_common()),
        "transcript_language_distribution": dict(transcript_language_distribution.most_common()),
    }
