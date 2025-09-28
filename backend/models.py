from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Word(Base):
    __tablename__ = "words"
    id = Column(Integer, primary_key=True)
    text = Column(String(5), unique=True, index=True)

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    word_id = Column(Integer, ForeignKey("words.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    attempts = Column(Integer, default=0)
    is_won = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    user = relationship("User")
    word = relationship("Word")

class Guess(Base):
    __tablename__ = "guesses"
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    guess_text = Column(String(5))
    feedback = Column(String)  # e.g., "GOXGX"
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game")
