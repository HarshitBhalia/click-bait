from __future__ import annotations

from collections.abc import Iterable

from googleapiclient.discovery import build


THUMBNAIL_PRIORITY = ("maxres", "standard", "high", "medium", "default")


def build_service(api_key: str):
    return build("youtube", "v3", developerKey=api_key, cache_discovery=False)


def get_uploads_playlist_id(service, channel_id: str) -> str:
    response = (
        service.channels()
        .list(part="contentDetails,snippet", id=channel_id, maxResults=1)
        .execute()
    )
    items = response.get("items", [])
    if not items:
        raise RuntimeError(f"Channel not found: {channel_id}")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def iter_playlist_video_ids(service, playlist_id: str, limit: int | None = None) -> Iterable[str]:
    seen = 0
    page_token = None
    while True:
        response = (
            service.playlistItems()
            .list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=min(limit - seen, 50) if limit else 50,
                pageToken=page_token,
            )
            .execute()
        )
        for item in response.get("items", []):
            yield item["contentDetails"]["videoId"]
            seen += 1
            if limit and seen >= limit:
                return
        page_token = response.get("nextPageToken")
        if not page_token:
            return


def _best_thumbnail_url(thumbnails: dict) -> str:
    for key in THUMBNAIL_PRIORITY:
        candidate = thumbnails.get(key)
        if candidate and candidate.get("url"):
            return candidate["url"]
    return ""


def fetch_video_metadata(service, video_ids: list[str]) -> list[dict]:
    rows: list[dict] = []
    for start in range(0, len(video_ids), 50):
        batch = video_ids[start : start + 50]
        response = (
            service.videos()
            .list(
                part="snippet,statistics,contentDetails",
                id=",".join(batch),
                maxResults=len(batch),
            )
            .execute()
        )
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            rows.append(
                {
                    "video_id": item.get("id", ""),
                    "channel_id": snippet.get("channelId", ""),
                    "channel_title": snippet.get("channelTitle", ""),
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "duration": item.get("contentDetails", {}).get("duration", ""),
                    "view_count": statistics.get("viewCount", 0),
                    "like_count": statistics.get("likeCount", 0),
                    "comment_count": statistics.get("commentCount", 0),
                    "thumbnail_url": _best_thumbnail_url(snippet.get("thumbnails", {})),
                    "default_language": snippet.get("defaultLanguage", ""),
                    "default_audio_language": snippet.get("defaultAudioLanguage", ""),
                    "tags": snippet.get("tags", []),
                    "collection_source": "youtube_api",
                }
            )
    return rows
