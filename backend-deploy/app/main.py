
from datetime import datetime
from pathlib   import Path
from typing    import List, Set

from fastapi                 import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles     import StaticFiles
from sqlalchemy.orm          import Session

from app.database import SessionLocal, init_db, Feedback, UserAnime
from app.schemas   import AniListProfileIn, FeedbackCreate, PlaylistResponse, VideoItem
from app.master_recommender import BigMasterRecommender

ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(title="AniMusic‑API", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "replace with deployed railway url here",   
        "http://localhost:8000"
    ],
    allow_origin_regex=r"^(chrome|moz)-extension://[a-z0-9]{32}$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")


init_db()
big = BigMasterRecommender()

def get_db():
    db = SessionLocal()
    try:    yield db
    finally: db.close()


@app.post("/upload_anilist_profile")
def upload_profile(p: AniListProfileIn, db: Session = Depends(get_db)):
    print(f"[playlist13]")
    print(f"[upload] {p.anilist_username}  {len(p.mal_ids)} MAL IDs") 
    print(f"[playlist12]")
    db.query(UserAnime).filter(UserAnime.anilist_username == p.anilist_username).delete()
    print(f"[playlist11]")
    for mid in p.mal_ids:
        db.add(UserAnime(anilist_username=p.anilist_username, mal_id=mid))
    print(f"[playlist10]")

    db.commit()
    print(f"[playlist14]")
    return {"status": "ok", "count": len(p.mal_ids)}

@app.post("/feedback")
def post_feedback(fb: FeedbackCreate, db: Session = Depends(get_db)):
    print(f"[feedback hit]")
    row = db.query(Feedback).filter(
            Feedback.anilist_username == fb.anilist_username,
            Feedback.song_id          == fb.song_id).first()

    if row: 
        print(f"[playlist6]")                                         
        row.watch_time       += fb.watch_time
        row.total_video_time  = max(row.total_video_time or 0, fb.total_video_time or 0)
        if fb.liked: row.liked = 1
        row.recommended_by   = fb.recommended_by
    else:
        print(f"[playlist7]")                                      
        db.add(Feedback(
            anilist_username = fb.anilist_username,
            song_id          = fb.song_id,
            recommended_by   = fb.recommended_by,
            watch_time       = fb.watch_time,
            total_video_time = fb.total_video_time,
            liked            = 1 if fb.liked else 0,
            timestamp        = datetime.utcnow()))
    print(f"[playlist8]")
    db.commit()
    print(f"[playlist9]")
    return {"status": "ok"}


@app.get("/playlist", response_model=PlaylistResponse)
def get_playlist(anilist_username: str, db: Session = Depends(get_db)):

    fb_rows = db.query(Feedback).filter(
                Feedback.anilist_username == anilist_username).all()


    mal_ids : Set[int] = {mid for (mid,) in
                          db.query(UserAnime.mal_id)
                            .filter(UserAnime.anilist_username == anilist_username)
                            .all()}


    recs = big.recommend(fb_rows, user_mal_ids=mal_ids)


    videos : List[VideoItem] = []
    for vid, label in recs:
        r = big.row.get(vid)
        if r is None: continue
        videos.append(VideoItem(
            youtube_video_id = vid,
            youtube_url      = f"https://youtube.com/watch?v={vid}",
            song             = r.get("song",""), anime = r.get("MAL_Title",""),
            recommended_by   = label))

    return PlaylistResponse(videos=videos)
