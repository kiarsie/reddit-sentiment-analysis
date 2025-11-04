from transformers import pipeline
from functools import lru_cache
import logging

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"

@lru_cache(maxsize=1)
def get_pipeline():
    # device = -1 for CPU, device=0 for GPU (use CPU if no GPU available)
    try:
        import torch
        device = 0 if torch.cuda.is_available() else -1
    except:
        device = -1  # Default to CPU if torch not available or no GPU
    pipe = pipeline("sentiment-analysis", model=MODEL_NAME, tokenizer=MODEL_NAME, device=device)
    logging.info(f"Loaded sentiment pipeline on device {device}")
    return pipe

# ACCEPTS DF AND ADD SENTIMENT AND CONFIDENCE (OPTIMIZED WITH BATCHING)
def analyze_dataframe(df):
    if df.empty:
        return df, {"positive": 0, "neutral": 0, "negative": 0}
    
    pipe = get_pipeline()
    texts = df["combined_text"].fillna("").astype(str).tolist()
    # Truncate each text to 512 chars
    texts = [text[:512] for text in texts]
    
    labels = []
    scores = []
    
    # Process in batches for speed (batch size 8 for CPU, 32 for GPU)
    batch_size = 32
    try:
        import torch
        if not torch.cuda.is_available():
            batch_size = 8  # Smaller batches for CPU
    except:
        batch_size = 8
    
    # Process all texts in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        try:
            results = pipe(batch, truncation=True, max_length=512)
            for result in results:
                label = result.get("label", "").lower()
                score = float(result.get("score", 0.0))
                if label.startswith("pos"):
                    label = "positive"
                elif label.startswith("neg"):
                    label = "negative"
                else:
                    label = "neutral"
                labels.append(label)
                scores.append(score)
        except Exception as e:
            # If batch fails, fall back to neutral for those items
            for _ in batch:
                labels.append("neutral")
                scores.append(0.0)
    
    df = df.copy()
    df["sentiment"] = labels
    df["confidence"] = scores
    counts = {
        "positive": int((df["sentiment"] == "positive").sum()),
        "neutral": int((df["sentiment"] == "neutral").sum()),
        "negative": int((df["sentiment"] == "negative").sum())
    }
    return df, counts
