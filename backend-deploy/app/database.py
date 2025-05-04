import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "replace with postgreql here"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


class Feedback(Base):
    __tablename__ = "feedback"
    id               = Column(Integer, primary_key=True, index=True)
    anilist_username = Column(String,  index=True, nullable=False)
    song_id          = Column(String,  index=True, nullable=False)
    recommended_by   = Column(String,  index=True, nullable=False)
    watch_time       = Column(Float,   default=0.0)
    total_video_time = Column(Float,   default=0.0)
    liked            = Column(Integer, default=0)
    timestamp        = Column(DateTime, default=datetime.utcnow)

class UserAnime(Base):
    __tablename__  = "user_anime"
    id              = Column(Integer, primary_key=True, index=True)
    anilist_username = Column(String,  index=True, nullable=False)
    mal_id           = Column(Integer, index=True, nullable=False)
    __table_args__   = (UniqueConstraint('anilist_username', 'mal_id'),)


def init_db():
    Base.metadata.create_all(bind=engine)
