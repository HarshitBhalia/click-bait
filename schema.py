from __future__ import annotations

import ast
from typing import Any


FIELD_ORDER = [
    "video_id",
    "channel_id",
    "channel_title",
    "channel_category",
    "title",
    "description",
    "published_at",
    "duration",
    "view_count",
    "like_count",
    "comment_count",
    "thumbnail_url",
    "thumbnail_path",
    "transcript_language",
    "transcript_available",
    "transcript_status",
    "transcript_checked",
    "transcript",
    "label",
    "label_status",
    "label_confidence",
    "collection_source",
    "notes",
    "heuristic_score",
    "auto_label",
    "default_audio_language",
    "default_language",
    "heuristic_reasons",
    "tags",
]

DEFAULT_RECORD = {
    "video_id": "",
    "channel_id": "",
    "channel_title": "",
    "channel_category": "",
    "title": "",
    "description": "",
    "published_at": "",
    "duration": "",
    "view_count": 0,
    "like_count": 0,
    "comment_count": 0,
    "thumbnail_url": "",
    "thumbnail_path": "",
    "transcript_language": "",
    "transcript_available": False,
    "transcript_status": "missing",
    "transcript_checked": False,
    "transcript": "",
    "label": None,
    "label_status": "",
    "label_confidence": None,
    "collection_source": "youtube_api",
    "notes": "",
    "heuristic_score": 0.0,
    "auto_label": None,
    "default_audio_language": "",
    "default_language": "",
    "heuristic_reasons": [],
    "tags": [],
}


def _as_int(value: Any) -> int | None:
    if value in ("", None):
        return None
    if isinstance(value, bool):
        return int(value)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value in (1, "1", "true", "True", "yes", "Yes"):
        return True
    return False


def _as_list(value: Any) -> list[str]:
    if value in ("", None):
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = ast.literal_eval(text)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed if str(item).strip()]
            except (SyntaxError, ValueError):
                pass
        if "|" in text:
            return [part.strip() for part in text.split("|") if part.strip()]
        if "," in text:
            return [part.strip() for part in text.split(",") if part.strip()]
        return [text]
    return [str(value)]


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(DEFAULT_RECORD)
    normalized.update(record or {})

    normalized["video_id"] = str(normalized["video_id"] or "").strip()
    normalized["channel_id"] = str(normalized["channel_id"] or "").strip()
    normalized["channel_title"] = str(normalized["channel_title"] or "").strip()
    normalized["channel_category"] = str(normalized["channel_category"] or "").strip()
    normalized["title"] = str(normalized["title"] or "").strip()
    normalized["description"] = str(normalized["description"] or "").strip()
    normalized["published_at"] = str(normalized["published_at"] or "").strip()
    normalized["duration"] = str(normalized["duration"] or "").strip()
    normalized["thumbnail_url"] = str(normalized["thumbnail_url"] or "").strip()
    normalized["thumbnail_path"] = str(normalized["thumbnail_path"] or "").strip()
    normalized["transcript_language"] = str(normalized["transcript_language"] or "").strip()
    normalized["transcript_status"] = str(normalized["transcript_status"] or "missing").strip()
    normalized["transcript"] = str(normalized["transcript"] or "").strip()
    normalized["label_status"] = str(normalized["label_status"] or "").strip()
    normalized["collection_source"] = str(normalized["collection_source"] or "youtube_api").strip()
    normalized["notes"] = str(normalized["notes"] or "").strip()
    normalized["default_audio_language"] = str(normalized["default_audio_language"] or "").strip()
    normalized["default_language"] = str(normalized["default_language"] or "").strip()

    normalized["view_count"] = _as_int(normalized["view_count"]) or 0
    normalized["like_count"] = _as_int(normalized["like_count"]) or 0
    normalized["comment_count"] = _as_int(normalized["comment_count"]) or 0
    normalized["label"] = _as_int(normalized["label"])
    normalized["auto_label"] = _as_int(normalized["auto_label"])
    normalized["label_confidence"] = _as_float(normalized["label_confidence"])
    normalized["heuristic_score"] = _as_float(normalized["heuristic_score"]) or 0.0
    normalized["transcript_available"] = _as_bool(normalized["transcript_available"])
    normalized["transcript_checked"] = _as_bool(normalized["transcript_checked"])
    normalized["heuristic_reasons"] = _as_list(normalized["heuristic_reasons"])
    normalized["tags"] = _as_list(normalized["tags"])

    return {field: normalized[field] for field in FIELD_ORDER}


def csv_ready_record(record: dict[str, Any]) -> dict[str, str]:
    normalized = normalize_record(record)
    csv_row: dict[str, str] = {}
    for field in FIELD_ORDER:
        value = normalized[field]
        if isinstance(value, list):
            if field == "tags":
                csv_row[field] = "|".join(value)
            else:
                csv_row[field] = repr(value)
        elif value is None:
            csv_row[field] = ""
        elif isinstance(value, bool):
            csv_row[field] = "True" if value else "False"
        else:
            csv_row[field] = str(value)
    return csv_row
