from __future__ import annotations

from typing import Any

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:  # pragma: no cover - dependency import guard
    YouTubeTranscriptApi = None


PREFERRED_LANGUAGES = ["hi", "en", "hi-IN", "en-IN"]


def _get_transcript_list(video_id: str):
    if YouTubeTranscriptApi is None:
        raise RuntimeError("youtube-transcript-api is not installed")
    if hasattr(YouTubeTranscriptApi, "list_transcripts"):
        return YouTubeTranscriptApi.list_transcripts(video_id)
    api = YouTubeTranscriptApi()
    if hasattr(api, "list_transcripts"):
        return api.list_transcripts(video_id)
    if hasattr(api, "list"):
        return api.list(video_id)
    raise RuntimeError("Unsupported youtube-transcript-api version")


def _candidate_transcripts(transcript_list, preferred_languages: list[str]) -> list[Any]:
    candidates: list[Any] = []
    methods = (
        "find_manually_created_transcript",
        "find_generated_transcript",
        "find_transcript",
    )
    for method_name in methods:
        method = getattr(transcript_list, method_name, None)
        if not method:
            continue
        try:
            transcript = method(preferred_languages)
        except Exception:
            transcript = None
        if transcript is not None:
            candidates.append(transcript)
    for transcript in transcript_list:
        candidates.append(transcript)
    return candidates


def fetch_best_transcript(video_id: str, preferred_languages: list[str] | None = None) -> dict:
    preferred = preferred_languages or PREFERRED_LANGUAGES
    try:
        transcript_list = _get_transcript_list(video_id)
        seen_codes: set[tuple[str, bool]] = set()
        for transcript in _candidate_transcripts(transcript_list, preferred):
            key = (getattr(transcript, "language_code", ""), bool(getattr(transcript, "is_generated", False)))
            if key in seen_codes:
                continue
            seen_codes.add(key)
            segments = transcript.fetch()
            text = " ".join(str(segment.get("text", "")).strip() for segment in segments if segment.get("text"))
            text = " ".join(text.split())
            if not text:
                continue
            return {
                "transcript": text,
                "transcript_language": getattr(transcript, "language_code", ""),
                "transcript_available": True,
                "transcript_checked": True,
                "transcript_status": "found",
            }
        return {
            "transcript": "",
            "transcript_language": "",
            "transcript_available": False,
            "transcript_checked": True,
            "transcript_status": "missing",
        }
    except Exception:
        return {
            "transcript": "",
            "transcript_language": "",
            "transcript_available": False,
            "transcript_checked": True,
            "transcript_status": "error",
        }
