import pandas as pd
from app.utils import clean_text
from app.config import COMMENT_LIMIT, TEXT_TRUNCATE


def build_df(submissions, include_comments: bool = True, max_comments: int = COMMENT_LIMIT):
    rows= []
    for s in submissions:
        title = s.title or ""
        selftext = (s.selftext or "").strip()
        comments_text = ""
        if include_comments:
            try: 
                submission_comments = s.comments.list()[:max_comments]
                comments_bodies = [c.body for c in submission_comments if hasattr(c, "body")]
                comments_text = " ".join(comments_bodies)
            except Exception:
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