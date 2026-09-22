import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
def _execute_with_retry(request):
    return request.execute()

# fetch top comments for a video
# returns a list of dicts, one per top-level comment, with reply_count but not the replies themselves
def get_comments(video_id: str, api_key: str, max_results: int = 100) -> list[dict]:
   
    youtube = build("youtube", "v3", developerKey=api_key)
    comments = []

    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_results,
            textFormat="plainText",
        )

        page_count = 0
        while request:
            response = _execute_with_retry(request)
            page_count += 1

            for item in response.get("items", []):
                top = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "comment_id": item["snippet"]["topLevelComment"]["id"],
                    "video_id": video_id,
                    "author": top.get("authorDisplayName"),
                    "text": top.get("textDisplay"),
                    "like_count": top.get("likeCount", 0),
                    "published_at": top.get("publishedAt"),
                    "updated_at": top.get("updatedAt"),
                    "reply_count": item["snippet"].get("totalReplyCount", 0),
                })

            request = youtube.commentThreads().list_next(request, response)

        logger.info(
            "Extracted %d comments from video %s across %d page(s)",
            len(comments), video_id, page_count,
        )

    # fetch errors
    except HttpError as e:
        logger.warning("Could not fetch comments for video %s: %s", video_id, e)

    return comments

# fetch comments for multiple videos (if there's more than 1 video) and combine them into a single list
def extract_all(video_ids: list[str], api_key: str, max_results: int = 100) -> list[dict]:
    all_comments = []
    for video_id in video_ids:
        all_comments.extend(get_comments(video_id, api_key, max_results))
    return all_comments