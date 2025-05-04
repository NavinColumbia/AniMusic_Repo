import os, pickle, pandas as pd
from sentence_transformers import SentenceTransformer


CSV_PATH      = "songs_final.csv" # change this one if you want to try locally 
MODEL_NAME    = "sentence-transformers/all-mpnet-base-v2"
EMBED_OUT     = "model_files/embeddings_mpnet.pkl"

os.makedirs("model_files", exist_ok=True)

def combine(row):
    txt = []
    for c in ["song","anime","vocals","lyrics","composition","arrangement",
              "tags","MAL_Genres"]:
        v = row.get(c,"")
        if isinstance(v,str):
            txt.append(v.strip())
    return " ".join(txt)


df = pd.read_csv(CSV_PATH).drop_duplicates(subset="youtube_video_id")
df["full_text"] = df.apply(combine, axis=1)


model = SentenceTransformer(MODEL_NAME)


emb = model.encode(df["full_text"].tolist(),
                   batch_size=32,
                   convert_to_numpy=True,
                   show_progress_bar=True)

with open(EMBED_OUT,"wb") as f:
    pickle.dump(
        {"video_ids": df["youtube_video_id"].astype(str).tolist(),
         "embeddings": emb,
         "model_name": MODEL_NAME},
        f)

