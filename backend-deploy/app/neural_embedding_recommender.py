import pickle, numpy as np, pandas as pd

from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent

class NeuralEmbeddingRecommender:

    def __init__(self,
                csv_path       = ROOT_DIR/"data"/"songs.csv",
                 embedding_path = ROOT_DIR/"model_files"/"embeddings.pkl"):
        self.df = pd.read_csv(csv_path).drop_duplicates(subset="youtube_video_id")
        self.df["youtube_video_id"] = self.df["youtube_video_id"].astype(str)

        with open(embedding_path, "rb") as f:
            data = pickle.load(f)
        self.video_ids  = data["video_ids"]
        self.embeddings = data["embeddings"].astype(np.float32)

        self.id2index   = {vid: i for i, vid in enumerate(self.video_ids)}

    def user_vector(self, liked: list[str] | None):
        idx = [self.id2index[v] for v in liked or [] if v in self.id2index]
        return None if not idx else self.embeddings[idx].mean(0)

    def _cos(self, a, b):
        d = np.linalg.norm(a) * np.linalg.norm(b)
        return float(np.dot(a, b) / d) if d else 0.0


    def recommend(self,
                  user_vec: np.ndarray | None,
                  candidate_ids: set[str] | None = None,
                  top_n: int = 50):
        if user_vec is None:
            return []
        cand = candidate_ids or self.video_ids
        sims = [(v, self._cos(user_vec, self.embeddings[self.id2index[v]]))
                for v in cand if v in self.id2index]
        sims.sort(key=lambda x: -x[1])
        return sims[:top_n]
