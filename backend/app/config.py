from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env from backend directory
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / ".env"
load_dotenv(dotenv_path=env_path)

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "reddit-movie-sentiment")

DEFAULT_SUBREDDIT = "stocks"
ALLOWED_SUBREDDITS = ["wallstreetbets", "stocks", "investing"]
POST_LIMIT_DEFAULT = 100  # Default number of posts to fetch (per subreddit when 'all')
POST_LIMIT_MAX = 100  # Maximum allowed posts (higher = more results but slower)
COMMENT_LIMIT = 10  # Number of comments per post to analyze (reduced for performance)
TEXT_TRUNCATE = 512
