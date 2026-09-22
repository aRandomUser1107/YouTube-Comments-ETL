import html
import logging
import re

import pandas as pd

logger = logging.getLogger(__name__)

def _clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Transform raw comment dicts into a cleaned DataFrame ready to load
# Steps:
# - Build DataFrame
# - Drop duplicate comments (can happen across re-runs / overlapping pages)
# - Parse timestamps into real datetime objects
# - Clean comment text
# - Enforce column types
def transform(raw_comments: list[dict]) -> pd.DataFrame:

    if not raw_comments:
        logger.warning("No comments to transform") # return empty
        return pd.DataFrame(columns=[
            "comment_id", "video_id", "author", "text",
            "like_count", "published_at", "updated_at", "reply_count",
        ])

    df = pd.DataFrame(raw_comments)

    before = len(df)
    df = df.drop_duplicates(subset="comment_id")
    logger.info("Dropped %d duplicate comment(s)", before - len(df))

    df["published_at"] = pd.to_datetime(df["published_at"], utc=True, errors="coerce")
    df["updated_at"] = pd.to_datetime(df["updated_at"], utc=True, errors="coerce")

    df["text"] = df["text"].apply(_clean_text)

    df["like_count"] = pd.to_numeric(df["like_count"], errors="coerce").fillna(0).astype(int)
    df["reply_count"] = pd.to_numeric(df["reply_count"], errors="coerce").fillna(0).astype(int)

    df = df.reset_index(drop=True)
    logger.info("Transformed %d comments", len(df))
    return df