import pandas as pd
from app.utils import clean_text
from app.config import COMMENT_LIMIT, TEXT_TRUNCATE
import logging

logger = logging.getLogger(__name__)

def build_df(submissions, include_comments: bool = True, max_comments: int = COMMENT_LIMIT):
    rows= []
    total = len(submissions)
    # Reduce comment limit when processing many posts to speed things up
    effective_comments = max_comments if total <= 50 else min(max_comments, 10)
    
    if include_comments and total > 20:
        logger.info(f"Processing {total} posts with comments (reduced to {effective_comments} comments/post for speed)")
    
    for idx, s in enumerate(submissions):
        if include_comments and idx % 10 == 0 and idx > 0:
            logger.info(f"Processing post {idx}/{total}...")
        
        title = s.title or ""
        selftext = (s.selftext or "").strip()
        comments_text = ""
        if include_comments:
            try:
                # Replace "MoreComments" objects - limit=0 means don't fetch more, just use what's loaded
                s.comments.replace_more(limit=0)
                # Get top-level comments only, faster than nested
                submission_comments = [c for c in s.comments.list() if hasattr(c, 'body')][:effective_comments]
                comments_bodies = [c.body for c in submission_comments if hasattr(c, 'body')]
                comments_text = " ".join(comments_bodies)
            except Exception as e:
                # Silently skip comments if there's an error (rate limit, deleted post, etc.)
                comments_text = ""
        
        combined = " ".join([title, selftext, comments_text])
        combined = clean_text(combined)[:TEXT_TRUNCATE]
        rows.append({
            "post_id": str(s.id),
            "title": title,
            "combined_text": combined,
            "url": f"https://www.reddit.com{s.permalink}",
            "subreddit": s.subreddit.display_name,
            "reddit_score": s.score
        })
    df = pd.DataFrame(rows)
    return df