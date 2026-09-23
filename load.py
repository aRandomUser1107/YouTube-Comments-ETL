import logging
 
import pandas as pd
import sqlalchemy as sa
 
logger = logging.getLogger(__name__)
 
TABLE_NAME = "comments"
 
# create the comments table with comment_id as primary key, if needed
def _ensure_table(engine: sa.Engine):
    metadata = sa.MetaData()
    sa.Table(
        TABLE_NAME,
        metadata,
        sa.Column("comment_id", sa.String, primary_key=True),
        sa.Column("video_id", sa.String, nullable=False),
        sa.Column("author", sa.String),
        sa.Column("text", sa.Text),
        sa.Column("like_count", sa.Integer),
        sa.Column("published_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
        sa.Column("reply_count", sa.Integer),
        sa.Column("sentiment_score", sa.Float),
        sa.Column("sentiment_label", sa.String),
    )
    metadata.create_all(engine)
 
# Load the DataFrame into the comments table, skipping comment_ids that already exist so the pipeline is safe to re-run (idempotent).
def load(df: pd.DataFrame, database_url: str):
    if df.empty:
        logger.warning("Nothing to load, DataFrame is empty")
        return
 
    engine = sa.create_engine(database_url)
    _ensure_table(engine)
 
    with engine.connect() as conn:
        existing_ids = {
            row[0] for row in conn.execute(sa.text(f"SELECT comment_id FROM {TABLE_NAME}"))
        }
 
    new_rows = df[~df["comment_id"].isin(existing_ids)]
 
    if new_rows.empty:
        logger.info("No new comments to insert, all %d already in DB", len(df))
        return
 
    new_rows.to_sql(TABLE_NAME, engine, if_exists="append", index=False)
    logger.info(
        "Inserted %d new comment(s) (%d were already in the database)",
        len(new_rows), len(df) - len(new_rows),
    )