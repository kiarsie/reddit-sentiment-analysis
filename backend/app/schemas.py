from pydantic import BaseModel
from typing import List, Dict

class PostOut(BaseModel):
    post_id: str
    title: str
    url: str
    subreddit: str
    reddit_score: int
    sentiment: str
    confidence: float

class AnalyzeResponse(BaseModel):
    query: str
    subreddit: str
    time_filter: str
    counts: Dict[str, int]
    posts: List[PostOut]
