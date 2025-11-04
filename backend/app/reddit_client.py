import praw 
from app.config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
from dotenv import load_dotenv
load_dotenv()

class RedditClient:
    def __init__(self):
        if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
            raise ValueError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set in environment variables")
        self.reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            check_for_async=False
        )
    # FETCH TOP 40 POSTS OF ALL TIME
    def fetch_top_posts(self, subreddit: str, limit: int = 40, time_filter: str = "all"):
        try:
            sub = self.reddit.subreddit(subreddit)
            # Test if we can access the subreddit
            _ = sub.display_name
            posts = list(sub.top(time_filter=time_filter, limit=limit))
            if not posts:
                raise ValueError(f"No posts found in r/{subreddit} with time_filter={time_filter}")
            return posts
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "Forbidden" in error_msg:
                raise ValueError(f"Access forbidden to r/{subreddit}. Check Reddit API permissions.")
            elif "404" in error_msg or "not found" in error_msg.lower():
                raise ValueError(f"Subreddit r/{subreddit} not found.")
            elif "401" in error_msg or "Unauthorized" in error_msg:
                raise ValueError("Reddit API authentication failed. Check your client_id and client_secret.")
            else:
                raise ValueError(f"Failed to fetch posts from r/{subreddit}: {error_msg}")
    
    # FETCH TOP 20 COMMENTS PER POST 
    def fetch_top_comments (self, submission, limit: int = 20):
        try: 
            submission.comments.replace_more(limit=0)
            comments = submission.comments.list()[:limit]
        except Exception:
            return[]