from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.reddit_client import RedditClient
from app.data_loader import build_dataframe
from app.sentiment_model import analyze_dataframe
from app.schemas import AnalyzeResponse, PostOut
from app.config import ALLOWED_SUBREDDITS, POST_LIMIT_DEFAULT, POST_LIMIT_MAX
from app.utils import simple_cache
import uvicorn

app = FastAPI(title="Reddit Movie Sentiment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

reddit = RedditClient()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/analyze", response_model=AnalyzeResponse)
@simple_cache(ttl_seconds=120)
async def analyze(
    query: str = Query(..., min_length=1),
    subreddit: str = Query("movies"),
    limit: int = Query(POST_LIMIT_DEFAULT, ge=1, le=POST_LIMIT_MAX),
    time_filter: str = Query("all")  # e.g., 'all', 'year'
):
    subreddit = subreddit.strip()
    if subreddit not in ALLOWED_SUBREDDITS:
        raise HTTPException(status_code=400, detail=f"subreddit must be one of {ALLOWED_SUBREDDITS}")

    # fetch posts
    submissions = reddit.fetch_top_posts(subreddit=subreddit, limit=limit, time_filter=time_filter)

    # build dataframe
    df = build_dataframe(submissions, include_comments=True)

    # filter posts by presence of query (simple title/selftext contains)
    if query:
        q = query.lower()
        df = df[df["combined_text"].str.lower().str.contains(q, na=False)]

    # run sentiment
    df_scored, counts = analyze_dataframe(df)

    # build posts output
    posts = []
    for _, row in df_scored.sort_values(by="reddit_score", ascending=False).iterrows():
        posts.append(PostOut(
            post_id=row["post_id"],
            title=row["title"],
            url=row["url"],
            subreddit=row["subreddit"],
            reddit_score=int(row["reddit_score"]),
            sentiment=row["sentiment"],
            confidence=float(row["confidence"])
        ))

    return AnalyzeResponse(
        query=query,
        subreddit=subreddit,
        time_filter=time_filter,
        counts=counts,
        posts=posts
    )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
