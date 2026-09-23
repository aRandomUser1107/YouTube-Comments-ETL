import logging

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

analyzer_obj = SentimentIntensityAnalyzer()

# Map VADER's compound score (-1 to 1)
def _score_to_label(compound_score: float) -> str:
    if compound_score >= 0.05:
        return "positive"
    elif compound_score <= -0.05:
        return "negative"
    return "neutral"

# add sentiment_score and sentiment_label columns based on the text column
def add_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df["sentiment_score"] = pd.Series(dtype="float64")
        df["sentiment_label"] = pd.Series(dtype="str")
        return df

    scores = df["text"].fillna("").apply(lambda t: analyzer_obj.polarity_scores(t)["compound"])
    df = df.copy()
    df["sentiment_score"] = scores
    df["sentiment_label"] = scores.apply(_score_to_label)

    logger.info(
        "Sentiment breakdown \n positive: %d, neutral: %d, negative: %d",
        (df["sentiment_label"] == "positive").sum(),
        (df["sentiment_label"] == "neutral").sum(),
        (df["sentiment_label"] == "negative").sum(),
    )
    return df