import os
import pandas as pd
import plotly.express as px
import sqlalchemy as sa
import streamlit as st
import yaml
 
st.set_page_config(page_title="YouTube Comments Dashboard", layout="wide")
 
 
@st.cache_data(ttl=60)
def load_data(database_url: str) -> pd.DataFrame:
    engine = sa.create_engine(database_url)
    df = pd.read_sql("SELECT * FROM comments", engine)
    df["published_at"] = pd.to_datetime(df["published_at"], utc=True, errors="coerce")
    return df
 
 
def get_database_url() -> str:
    if os.path.exists("config.yaml"):
        with open("config.yaml") as f:
            config = yaml.safe_load(f)
        return config.get("database_url", "sqlite:///data/youtube_comments.db")
    return "sqlite:///data/youtube_comments.db"
 
 
st.title("YouTube Comments Dashboard")
 
database_url = get_database_url()
 
if not os.path.exists(database_url.replace("sqlite:///", "")):
    st.warning(
        "Database not found. Run `python etl.py` to create the database and load comments."
    )
    st.stop()
 
df = load_data(database_url)
 
if df.empty:
    st.warning("No comments found in the database. Run `python etl.py` to load comments.")
    st.stop()
 

st.sidebar.header("Filters")
 
video_options = ["All videos"] + sorted(df["video_id"].unique().tolist())
selected_video = st.sidebar.selectbox("Video", video_options)
 
if selected_video != "All videos":
    df = df[df["video_id"] == selected_video]
 
st.sidebar.metric("Total comments", len(df))
if "sentiment_label" in df.columns:
    st.sidebar.metric("Avg. sentiment score", f"{df['sentiment_score'].mean():.2f}")
 

col1, col2, col3, col4 = st.columns(4)
col1.metric("Comments", len(df))
col2.metric("Unique commenters", df["author"].nunique())
col3.metric("Total likes", int(df["like_count"].sum()))
if "sentiment_label" in df.columns and not df["sentiment_label"].isna().all():
    top_sentiment = df["sentiment_label"].value_counts().idxmax()
    col4.metric("Most common sentiment", top_sentiment.capitalize())
 
st.divider()
 
st.subheader("Comments over time")
 
daily = (
    df.dropna(subset=["published_at"])
    .set_index("published_at")
    .resample("D")
    .size()
    .reset_index(name="comment_count")
)
 
if daily.empty:
    st.info("Not enough dated comments to show a trend yet.")
else:
    fig_time = px.line(
        daily, x="published_at", y="comment_count",
        markers=True, labels={"published_at": "Date", "comment_count": "Comments"},
    )
    st.plotly_chart(fig_time, use_container_width=True)
 
st.divider()

st.subheader("Top commenters")
 
col_a, col_b = st.columns(2)
 
with col_a:
    st.caption("By number of comments")
    top_by_count = (
        df["author"].value_counts().head(10).reset_index()
    )
    top_by_count.columns = ["author", "comment_count"]
    fig_count = px.bar(
        top_by_count, x="comment_count", y="author",
        orientation="h", labels={"comment_count": "Comments", "author": ""},
    )
    fig_count.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_count, use_container_width=True)
 
with col_b:
    st.caption("By total likes received")
    top_by_likes = (
        df.groupby("author")["like_count"].sum()
        .sort_values(ascending=False).head(10).reset_index()
    )
    fig_likes = px.bar(
        top_by_likes, x="like_count", y="author",
        orientation="h", labels={"like_count": "Total likes", "author": ""},
    )
    fig_likes.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_likes, use_container_width=True)
 
st.divider()

if "sentiment_label" in df.columns and not df["sentiment_label"].isna().all():
    st.subheader("Sentiment trends")
 
    col_c, col_d = st.columns([1, 2])
 
    with col_c:
        st.caption("Overall breakdown")
        sentiment_counts = df["sentiment_label"].value_counts().reset_index()
        sentiment_counts.columns = ["sentiment", "count"]
        fig_pie = px.pie(
            sentiment_counts, names="sentiment", values="count",
            color="sentiment",
            color_discrete_map={"positive": "#2ecc71", "neutral": "#95a5a6", "negative": "#e74c3c"},
        )
        st.plotly_chart(fig_pie, use_container_width=True)
 
    with col_d:
        st.caption("Sentiment over time")
        sentiment_daily = (
            df.dropna(subset=["published_at"])
            .set_index("published_at")
            .groupby("sentiment_label")
            .resample("D")
            .size()
            .reset_index(name="count")
        )
        if sentiment_daily.empty:
            st.info("Not enough dated comments to show a sentiment trend yet.")
        else:
            fig_sentiment_time = px.line(
                sentiment_daily, x="published_at", y="count", color="sentiment_label",
                labels={"published_at": "Date", "count": "Comments", "sentiment_label": "Sentiment"},
                color_discrete_map={"positive": "#2ecc71", "neutral": "#95a5a6", "negative": "#e74c3c"},
            )
            st.plotly_chart(fig_sentiment_time, use_container_width=True)
else:
    st.info(
        "Sentiment analysis has not been run yet. Run `python etl.py` to analyze comment sentiment."
    )
 
st.divider()

with st.expander("Browse raw comments"):
    sort_col = st.selectbox(
        "Sort by", ["published_at", "like_count", "sentiment_score"],
        index=1 if "like_count" in df.columns else 0,
    )
    st.dataframe(
        df.sort_values(sort_col, ascending=False)[
            [c for c in ["author", "text", "like_count", "published_at",
                         "sentiment_label", "sentiment_score"] if c in df.columns]
        ],
        use_container_width=True,
    )