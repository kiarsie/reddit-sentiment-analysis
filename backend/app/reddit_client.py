import praw 
from app.config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
from dotenv import load_dotenv
load_dotenv()

class RedditClient:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            check_for_async=False
        )
    # FETCH TOP 40 POSTS OF ALL TIME
    def fetch_top_posts(self, subreddit: str, limit: int = 40, time_filter: str = "all"):
        sub = self.reddit.subreddit(subreddit)
        return list(sub.top(time_filter=time_filter, limit=limit))
    
    # FETCH TOP 20 COMMENTS PER POST 
    def fetch_top_comments (self, submission, limit: int = 20):
        try: 
            submission.commentsz.replace_more(limit=0)
            comments = submission.comments.list()[:limit]
        except Exception:
            return[]