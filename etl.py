import logging
import os

import yaml
from dotenv import load_dotenv

from extract import extract_all
from transform import transform
from load import load

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def run():
    load_dotenv()
    api_key = os.getenv("API_KEY")

    if not api_key or api_key == "your_api_key_here":
        raise RuntimeError(
            "YouTube API Key is not set"
        )

    config = load_config()
    video_ids = config["video_ids"]
    max_results = config.get("max_results_per_page", 100)
    database_url = config.get("database_url", "sqlite:///data/youtube_comments.db")

    logger.info("Starting ETL run for %d video(s)", len(video_ids))

    # Extract
    raw_comments = extract_all(video_ids, api_key, max_results)
    logger.info("Extract complete: %d raw comment(s)", len(raw_comments))

    # Transform
    df = transform(raw_comments)
    logger.info("Transform complete: %d cleaned comment(s)", len(df))

    # Load
    load(df, database_url)
    logger.info("ETL run finished")


if __name__ == "__main__":
    run()