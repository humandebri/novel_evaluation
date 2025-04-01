from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Novel(Base):
    __tablename__ = "novels"
    
    id = Column(String(20), primary_key=True)  # Kakuyomu work ID
    title = Column(String(255), nullable=False)
    author = Column(String(100), nullable=False)
    ranking_position = Column(Integer, nullable=False)
    novel_url = Column(String(512), nullable=False)
    genre = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    episodes = relationship("Episode", back_populates="novel")
    evaluations = relationship("Evaluation", back_populates="novel")

class Episode(Base):
    __tablename__ = "episodes"
    
    id = Column(String(50), primary_key=True)  # Kakuyomu episode ID
    novel_id = Column(String(20), ForeignKey("novels.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    posted_at = Column(DateTime, nullable=False)
    
    novel = relationship("Novel", back_populates="episodes")

class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(String(20), ForeignKey("novels.id"), nullable=False)
    episode_id = Column(String(50), ForeignKey("episodes.id"))
    evaluation_date = Column(DateTime, default=datetime.utcnow)
    overall_score = Column(Float, nullable=False)
    story_score = Column(Float)
    writing_score = Column(Float)
    character_score = Column(Float)
    llm_feedback = Column(Text)
    
    novel = relationship("Novel", back_populates="evaluations")
    episode = relationship("Episode")
