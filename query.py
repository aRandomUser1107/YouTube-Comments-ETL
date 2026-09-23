import sqlalchemy as sa
import pandas as pd

engine = sa.create_engine("sqlite:///data/youtube_comments.db")
df = pd.read_sql(
    "SELECT author, text, sentiment_label, sentiment_score FROM comments WHERE sentiment_label = 'positive' LIMIT 10",
    engine,
)
print(df)