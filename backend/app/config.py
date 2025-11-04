from dotenv import load_dotenv
import os

load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "reddit-movie-sentiment")

DEFAULT_SUBREDDIT = "movies"
ALLOWED_SUBREDDIT = ["movies", "TrueFilm", "boxoffice"]
POST_LIMIT_DEFAULT = 40
POST_LIMIT_MAX = 50
COMMENT_LIMIT = 20
TEXT_TRUNCATE = 512
