from transformers import pipeline
from functools import lru_cache
import logging

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"

@lru_cache(maxsize=1)
def get_pipeline():
    # device = -1 for CPU device=0 for GPU
    pipe = pipeline("sentiment-analysis", model=MODEL_NAME, tokenizer=MODEL_NAME, device=0)
    logging.info("Loaded sentiment pipeline")
    return pipe

# ACCEPTS DF AND ADD SENTIMENT AND CONFIDENCE
def analyze_dataframe(df):
    pipe = get_pipeline()
    labels = []
    scores = []
    for text in df["combined_text"].fillna("").astype(str).tolist():
        try:
            out = pipe(text[:512])[0]
            label = out.get("label", "").lower()
            score = float(out.get("score", 0.0))
            if label.startswith("pos"):
                label = "positive"
            elif label.startswith("neg"):
                label = "negative"
            else:
                label = "neutral"
        except Exception:
            label = "neutral"
            score = 0.0
        labels.append(label)
        scores.append(score)
    df = df.copy()
    df["sentiment"] = labels
    df["confidence"] = scores
    counts = {
        "positive": int((df["sentiment"] == "positive").sum()),
        "neutral": int((df["sentiment"] == "neutral").sum()),
        "negative": int((df["sentiment"] == "negative").sum())
    }
    return df, counts
