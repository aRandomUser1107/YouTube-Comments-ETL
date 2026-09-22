import sqlalchemy as sa
import pandas as pd

engine = sa.create_engine("sqlite:///data/youtube_comments.db")
df = pd.read_sql(
    "SELECT author, text, like_count FROM comments ORDER BY like_count DESC LIMIT 10",
    engine,
)
print(df)