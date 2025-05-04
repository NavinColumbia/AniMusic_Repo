
import random, re, numpy as np
from typing import Iterable, Tuple, List, Set
from pathlib import Path

from app.models import RecommenderSystem
from app.neural_embedding_recommender import NeuralEmbeddingRecommender
from app.neural_embedding_recommender_mpnet import MPNetRecommender

ROOT_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT_DIR / "data" / "songs.csv"

Pick = Tuple[str, str] 

def root(name: str) -> str:
    return re.sub(r"\s+", " ", name.lower()).strip()

class BigMasterRecommender:
    BUCKETS = ("mpnet", "minilm", "node2vec", "tfidf", "popular", "random")

    def __init__(self, csv=CSV_PATH):
        self.rs     = RecommenderSystem(csv, ROOT_DIR / "model_files", True)
        self.mini   = NeuralEmbeddingRecommender(csv)
        self.mpnet  = MPNetRecommender(csv)

        self.df = self.rs.df
        if "combined_text" not in self.df.columns:
            self.df["combined_text"] = self.df.apply(
                lambda r: " ".join(str(r.get(c, "")) for c in
                    ("song", "anime", "vocals", "composition", "arrangement",
                     "tags", "MAL_Genres")), axis=1)

        self.row  = {str(r["youtube_video_id"]): r for _, r in self.df.iterrows()}
        self.all  = set(self.row)

    def _anime(self, vid: str) -> str:
        r = self.row.get(vid)
        return "" if r is None else root(str(r.get("MAL_Title", "")))


    def _llm(self, model, liked, pool):
        u = model.user_vector(liked) if liked else np.mean(model.embeddings, 0)
        for vid, _ in model.recommend(u, pool, 300): yield vid

    def _node(self, liked, pool):
        for vid, _ in self.rs.recommend_node2vec(liked, 300):
            if vid in pool: yield vid

    def _tfidf(self, seed_text: str, pool):
        if not seed_text.strip(): return
        for vid, _ in self.rs.recommend_tfidf(seed_text, 300):
            if vid in pool: yield vid

    def _popular(self, pool):
        for vid, _ in self.rs.recommend_popular(300):
            if vid in pool: yield vid

    def _random(self, pool):
        pool = list(pool); random.shuffle(pool); yield from pool

    def recommend(self,
                  feedback: Iterable,
                  user_mal_ids: Set[int],
                  size: int = 6) -> List[Pick]:

        #  skip list, per-anime score 
        skip, score = set(), {}
        for fb in feedback:
            skip.add(fb.song_id)
            anime = self._anime(fb.song_id)
            if not anime: continue
            good = fb.liked or (fb.total_video_time and
                                fb.watch_time >= 0.5 * fb.total_video_time)
            score[anime] = score.get(anime, 0) + (1 if good else -1)

        blacklist = {a for a, s in score.items() if s < 0}

        def allowed(v): return self._anime(v) not in blacklist
        pool = {v for v in (self.all - skip) if allowed(v)} or \
               (self.all - skip) or self.all


        liked = [fb.song_id for fb in feedback
                 if fb.liked or (fb.total_video_time and
                                 fb.watch_time >= 0.5 * fb.total_video_time)]

        if not liked and user_mal_ids:
            liked.extend(self.df[self.df.MAL_ID.isin(user_mal_ids)]
                         ["youtube_video_id"].head(20).tolist())

        seed_text = " ".join(self.df[self.df.youtube_video_id.isin(liked)]
                             ["combined_text"])

        streams = {
            "mpnet"   : self._llm(self.mpnet , liked, pool),
            "minilm"  : self._llm(self.mini  , liked, pool),
            "node2vec": self._node(liked, pool),
            "tfidf"   : self._tfidf(seed_text, pool),
            "popular" : self._popular(pool),
            "random"  : self._random(pool),
        }

        used_vids, used_anime, playlist = set(), set(), []

        for label in self.BUCKETS:
            for vid in streams[label]:
                anime = self._anime(vid)
                if vid in used_vids or anime in used_anime: continue
                used_vids.add(vid); used_anime.add(anime)
                playlist.append((vid, label))
                break

        return playlist[:size]

