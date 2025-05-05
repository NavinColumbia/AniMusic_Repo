
import pandas as pd
import pickle
import os
from sentence_transformers import SentenceTransformer

CSV_PATH = "songs.csv"
MODEL_OUTPUT = "model_files/embeddings.pkl"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

os.makedirs("model_files", exist_ok=True)

def combine_fields(row):
    fields = []
    for c in ["song", "anime", "vocals", "lyrics", "composition", "arrangement", "tags", "MAL_Genres"]:
        val = row.get(c, "")
        if isinstance(val, str):
            fields.append(val.strip())
    return " ".join(fields)

def main():
    df = pd.read_csv(CSV_PATH)
    df.drop_duplicates(subset="youtube_video_id", inplace=True)
    df["youtube_video_id"] = df["youtube_video_id"].astype(str)

    df["full_text"] = df.apply(combine_fields, axis=1)

    model = SentenceTransformer(MODEL_NAME)

    corpus = df["full_text"].tolist()
    embeddings = model.encode(corpus, batch_size=32, convert_to_numpy=True, show_progress_bar=True)

    meta = {
        "video_ids": df["youtube_video_id"].tolist(),
        "embeddings": embeddings,
        "model_name": MODEL_NAME
    }

    with open(MODEL_OUTPUT, "wb") as f:
        pickle.dump(meta, f)

if __name__ == "__main__":
    main()
