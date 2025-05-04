# models.py
import pandas as pd
import numpy as np
import networkx as nx
import os, pickle
from node2vec import Node2Vec
from sklearn.feature_extraction.text import TfidfVectorizer

from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent

def parse_views(x):
    if isinstance(x,(int,float)):
        return x
    if not isinstance(x,str):
        return 0
    s=x.strip().lower()
    if s.endswith('k'):
        try: return float(s[:-1])*1000
        except: return 0
    elif s.endswith('m'):
        try: return float(s[:-1])*1000000
        except: return 0
    else:
        try:
            return float(s)
        except:
            return 0

class RecommenderSystem:
    def __init__(self, 
                csv_path   = ROOT_DIR / "data" / "songs.csv",
                 pkl_folder = ROOT_DIR / "model_files",
                 
                  use_precomputed=True):
        self.csv_path=csv_path
        self.pkl_folder=pkl_folder
        os.makedirs(self.pkl_folder, exist_ok=True)
        self.pkl_path=os.path.join(self.pkl_folder,"recommender.pkl")

        self.df=pd.DataFrame()
        self.n2v_model=None
        self.tfidf_matrix=None
        self.tfidf_vectorizer=None
        self.video_ids_tfidf=None
        self.graph=None

        self._load_or_build(use_precomputed)

    def _load_or_build(self, use_precomputed):
        try:
            self.df=pd.read_csv(self.csv_path)
        except Exception as e:
            print(" csv error :", e)
            return

        if "youtube_views" in self.df.columns:
            self.df["youtube_views"]=self.df["youtube_views"].apply(parse_views)
        else:
            self.df["youtube_views"]=0

        def fix_likes(row):
            val=row.get("youtube_likes","")
            if isinstance(val,(int,float)):
                return val
            if not isinstance(val,str):
                return 0.1*row["youtube_views"]
            s=val.strip().lower()
            if s in("like","likes","","nan"):
                return 0.1*row["youtube_views"]
            try:
                return float(s)
            except:
                return 0.1*row["youtube_views"]
        if "youtube_likes" in self.df.columns:
            self.df["youtube_likes"]=self.df.apply(fix_likes, axis=1)
        else:
            self.df["youtube_likes"]=self.df["youtube_views"]/10

        self.df["popularity_score"]=np.log1p(self.df["youtube_views"].clip(lower=0))

        self.df.drop_duplicates(subset="youtube_video_id", inplace=True)
        self.df["youtube_video_id"]=self.df["youtube_video_id"].astype(str)
        junk={"youtube_views","MAL_SCORE","NaN","nan",""}
        self.df=self.df[~self.df["youtube_video_id"].isin(junk)]

        print(f"[RecommenderSystem] loaded {len(self.df)} songs from {self.csv_path}")

        if use_precomputed and os.path.exists(self.pkl_path):
            try:
                with open(self.pkl_path,"rb") as f:
                    data=pickle.load(f)
                self.n2v_model=data["n2v_model"]
                self.graph=data["graph"]
                self.tfidf_matrix=data["tfidf_matrix"]
                self.video_ids_tfidf=data["video_ids_tfidf"]
                self.tfidf_vectorizer=data["tfidf_vectorizer"]
                print("[RecommenderSystem] loaded from pkl:", self.pkl_path)
                return
            except Exception as e:
                print("[RecommenderSystem] load pkl error:", e)

        self._build_tfidf()
        self._build_node2vec()
        self._save()

    def _save(self):
        data={
            "n2v_model": self.n2v_model,
            "graph": self.graph,
            "tfidf_matrix": self.tfidf_matrix,
            "video_ids_tfidf": self.video_ids_tfidf,
            "tfidf_vectorizer": self.tfidf_vectorizer
        }
        try:
            with open(self.pkl_path,"wb") as f:
                pickle.dump(data,f)
            print("[RecommenderSystem] saved to =>", self.pkl_path)
        except Exception as e:
            print("[RecommenderSystem] pkl save error:", e)

    def _build_tfidf(self):
        if "youtube_video_id" not in self.df.columns:
            print("[RecommenderSystem] no youtube_video_id => skip TF-IDF")
            return
        from sklearn.metrics.pairwise import cosine_similarity

        def combine_text(row):
            fields=[]
            for c in ["song","anime","vocals","composition","arrangement","tags","MAL_Genres"]:
                val=row.get(c,"")
                if isinstance(val,str):
                    fields.append(val.lower().strip())
            return " ".join(fields)

        self.df["combined_text"]=self.df.apply(combine_text,axis=1)
        grouped=self.df.groupby("youtube_video_id")["combined_text"].apply(lambda x:" ".join(x)).reset_index()
        self.video_ids_tfidf=grouped["youtube_video_id"].values

        self.tfidf_vectorizer=TfidfVectorizer(stop_words="english")
        self.tfidf_matrix=self.tfidf_vectorizer.fit_transform(grouped["combined_text"])
        print("[RecommenderSystem] TF-IDF shape:", self.tfidf_matrix.shape)

    def _build_node2vec(self):
        G=nx.Graph()
        for idx,row in self.df.iterrows():
            vid=str(row.get("youtube_video_id",""))
            if not vid: 
                continue
            G.add_node(vid, ntype="song")

            anime=str(row.get("anime","")).strip().lower()
            if anime:
                G.add_node(anime, ntype="anime")
                G.add_edge(vid, anime, weight=1.0)
            comp=str(row.get("composition",""))
            comp=comp.strip().lower()
            if comp and comp not in("nan",""):
                G.add_node(comp, ntype="composer")
                G.add_edge(vid, comp, weight=1.0)
            tagsVal=row.get("tags","")
            if isinstance(tagsVal,str):
                for t in tagsVal.split(","):
                    t2=t.strip().lower()
                    if t2 and t2 not in("nan",""):
                        G.add_node(t2, ntype="tag")
                        G.add_edge(vid, t2, weight=1.0)

        if G.number_of_nodes()<2:
            print(" insufficient data for node2vec ")
            return
        node2v=Node2Vec(G, dimensions=16, walk_length=10, num_walks=20, workers=1,quiet=True)
        self.n2v_model=node2v.fit(window=5, min_count=1, batch_words=4)
        self.graph=G

    def recommend_tfidf(self, user_text:str, top_n=200):
        if self.tfidf_matrix is None or self.tfidf_matrix.shape[0] == 0 or not user_text.strip():
            return []
        from sklearn.metrics.pairwise import cosine_similarity
        user_vec=self.tfidf_vectorizer.transform([user_text])
        sims=cosine_similarity(user_vec,self.tfidf_matrix)[0]
        idxs=np.argsort(-sims)[:top_n]
        recs=[]
        for i in idxs:
            vid=self.video_ids_tfidf[i]
            recs.append((vid,float(sims[i])))
        return recs

    def recommend_node2vec(self, user_items:list, top_n=200):
        if not self.n2v_model or not user_items:
            return []
        import numpy as np
        from numpy.linalg import norm
        from numpy import dot

        vecs=[]
        for it in user_items:
            if it in self.n2v_model.wv:
                vecs.append(self.n2v_model.wv[it])
        if not vecs:
            return []
        avg=np.mean(vecs,axis=0)
        results=[]
        for node in self.graph.nodes():
            if self.graph.nodes[node].get("ntype")=="song" and node in self.n2v_model.wv:
                emb=self.n2v_model.wv[node]
                denom=norm(avg)*norm(emb)
                if denom>0:
                    sim=float(dot(avg,emb)/denom)
                else:
                    sim=0.0
                results.append((node, sim))
        results.sort(key=lambda x:x[1],reverse=True)
        return results[:top_n]

    def recommend_popular(self, top_n=200):
        sorted_df=self.df.sort_values("popularity_score", ascending=False)
        recs=[]
        for i,row in sorted_df.head(top_n).iterrows():
            vid=row["youtube_video_id"]
            recs.append((vid,float(row["popularity_score"])))
        return recs

    def recommend_random_from_subset(self, subset_ids, top_n=200):
        import random
        arr=list(subset_ids)
        random.shuffle(arr)
        return [(vid,0.0) for vid in arr[:top_n]]

    def get_anime_for(self, vid:str):
        row=self.df[self.df["youtube_video_id"]==vid].head(1)
        if row.empty:
            return ""
        return str(row.iloc[0]["anime"]).strip().lower()

    def get_animes_for_malids(self, mal_ids:list):
        if "MAL_ID" not in self.df.columns:
            return set()
        subset = self.df[self.df["MAL_ID"].isin(mal_ids)]
        animes = set( str(r["anime"]).strip().lower() for _,r in subset.iterrows() if r["anime"] )
        return animes
