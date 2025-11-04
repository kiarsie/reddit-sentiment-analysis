from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.reddit_client import RedditClient
from app.data_loader import build_df
from app.sentiment_model import analyze_dataframe
from app.schemas import AnalyzeResponse, PostOut
from app.config import ALLOWED_SUBREDDITS, POST_LIMIT_DEFAULT, POST_LIMIT_MAX
from app.utils import simple_cache
import uvicorn
import asyncio
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Reddit Stock Sentiment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://reddit-sentiment-analysis-ake41z3kd-kiarsies-projects.vercel.app"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy initialization - create client only when needed
_reddit_client = None

def get_reddit_client():
    global _reddit_client
    if _reddit_client is None:
        try:
            _reddit_client = RedditClient()
            logger.info("Reddit client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Reddit client initialization failed: {str(e)}")
    return _reddit_client

@app.get("/")
async def root():
    return {"message": "Reddit Movie Sentiment API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "ok", "message": "API is running"}

@app.get("/test")
async def test():
    """Simple test endpoint"""
    return {"message": "Test successful", "status": "ok"}

@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check if Reddit credentials are loaded (without exposing secrets)"""
    from app.config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
    return {
        "has_client_id": bool(REDDIT_CLIENT_ID),
        "has_client_secret": bool(REDDIT_CLIENT_SECRET),
        "user_agent": REDDIT_USER_AGENT,
        "client_id_length": len(REDDIT_CLIENT_ID) if REDDIT_CLIENT_ID else 0
    }

@app.get("/analyze", response_model=AnalyzeResponse)
@simple_cache(ttl_seconds=120)
async def analyze(
    query: str = Query(..., min_length=1),
    subreddit: str = Query("all"),
    limit: int = Query(POST_LIMIT_DEFAULT, ge=1, le=POST_LIMIT_MAX),
    time_filter: str = Query("all"),  # e.g., 'all', 'year'
    include_comments: bool = Query(False)  # Default False for speed - set True if you want comments
):
    subreddit = subreddit.strip()
    # Support 'all' to search across every allowed subreddit
    if subreddit != "all" and subreddit not in ALLOWED_SUBREDDITS:
        raise HTTPException(status_code=400, detail=f"subreddit must be 'all' or one of {ALLOWED_SUBREDDITS}")

    try:
        # Run blocking operations in thread pool to avoid blocking the event loop
        logger.info(f"Starting analysis for query: '{query}', subreddit: {subreddit}, limit per subreddit: {limit}")
        
        # Step 1: Fetch posts (blocking, run in thread pool)
        reddit = get_reddit_client()
        loop = asyncio.get_event_loop()
        logger.info("Fetching Reddit posts...")
        submissions = []
        if subreddit == "all":
            # Fetch 'limit' posts per allowed subreddit
            tasks = [
                loop.run_in_executor(None, reddit.fetch_top_posts, sub, limit, time_filter)
                for sub in ALLOWED_SUBREDDITS
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for sub, res in zip(ALLOWED_SUBREDDITS, results):
                if isinstance(res, Exception):
                    logger.warning(f"Fetch failed for r/{sub}: {res}")
                    continue
                submissions.extend(res)
            logger.info(f"Fetched total {len(submissions)} posts across {len(ALLOWED_SUBREDDITS)} subreddits")
        else:
            submissions = await loop.run_in_executor(
                None,
                reddit.fetch_top_posts,
                subreddit, limit, time_filter
            )
            logger.info(f"Fetched {len(submissions)} posts from r/{subreddit}")

        # Step 2: Build dataframe (blocking, run in thread pool)
        logger.info("Building dataframe...")
        df = await loop.run_in_executor(
            None,
            build_df,
            submissions, include_comments
        )
        logger.info(f"Dataframe built with {len(df)} rows")

        # Step 3: Filter by query
        if query:
            q = query.lower()
            df = df[df["combined_text"].str.lower().str.contains(q, na=False)]
            logger.info(f"Filtered to {len(df)} rows matching query")

        if df.empty:
            return AnalyzeResponse(
                query=query,
                subreddit=subreddit,
                time_filter=time_filter,
                counts={"positive": 0, "neutral": 0, "negative": 0},
                posts=[]
            )

        # Step 4: Run sentiment analysis (blocking, run in thread pool)
        logger.info("Running sentiment analysis...")
        df_scored, counts = await loop.run_in_executor(
            None,
            analyze_dataframe,
            df
        )
        logger.info("Sentiment analysis complete")

        # Step 5: Build response
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

        logger.info(f"Returning {len(posts)} posts")
        return AnalyzeResponse(
            query=query,
            subreddit=subreddit,
            time_filter=time_filter,
            counts=counts,
            posts=posts
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # fallback to 8080 for local dev
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
