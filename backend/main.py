# backend/main.py
import os
from datetime import datetime, date
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Query, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import (Column, Integer, String, Boolean, DateTime, ForeignKey,
                        create_engine, func)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session

# -----------------------
# Config
# -----------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # project root
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
DB_FILE = os.path.join(os.path.dirname(__file__), "guessword.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_FILE}"

SECRET_KEY = "change_this_to_a_random_secret_in_prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -----------------------
# DB setup
# -----------------------
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# -----------------------
# Models
# -----------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    games = relationship("Game", back_populates="user")

class Word(Base):
    __tablename__ = "words"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(5), unique=True, nullable=False)

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    word_id = Column(Integer, ForeignKey("words.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    attempts = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_won = Column(Boolean, default=False)
    user = relationship("User", back_populates="games")
    word = relationship("Word")
    guesses = relationship("Guess", back_populates="game")

class Guess(Base):
    __tablename__ = "guesses"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    guess_text = Column(String(5), nullable=False)
    feedback = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    game = relationship("Game", back_populates="guesses")

# -----------------------
# Pydantic schemas
# -----------------------
class RegisterIn(BaseModel):
    username: str
    password: str
    is_admin: Optional[bool] = False

class LoginIn(BaseModel):
    username: str
    password: str

class StartGameOut(BaseModel):
    game_id: int

class GuessIn(BaseModel):
    game_id: int
    guess: str

class GuessOut(BaseModel):
    feedback: List[str]
    attempts: int
    is_won: bool
    is_active: bool

# -----------------------
# Utility functions
# -----------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def hash_password(password):
    return pwd_context.hash(password)

def create_token(data: dict):
    to_encode = data.copy()
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# -----------------------
# Game logic
# -----------------------
def evaluate_guess(secret: str, guess: str) -> List[str]:
    secret = secret.upper()
    guess = guess.upper()
    result = ["absent"] * 5
    secret_counts = {}

    for i in range(5):
        s = secret[i]
        secret_counts[s] = secret_counts.get(s, 0) + 1

    for i in range(5):
        if guess[i] == secret[i]:
            result[i] = "correct"
            secret_counts[guess[i]] -= 1

    for i in range(5):
        if result[i] == "correct":
            continue
        ch = guess[i]
        if secret_counts.get(ch, 0) > 0:
            result[i] = "present"
            secret_counts[ch] -= 1
        else:
            result[i] = "absent"
    return result

# -----------------------
# App
# -----------------------
app = FastAPI(title="Guess Word Game API")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "ADMIN").first()
        if not admin:
            db.add(User(username="ADMIN", password_hash=hash_password("Admin1@"), is_admin=True))
        seed = [
            "APPLE","BERRY","CHILI","DELTA","EAGLE","FRUIT","GRAPE","HOUSE","IRONY","JOKER",
            "KNIFE","LEMON","MANGO","NINJA","OCEAN","PILOT","QUART","RIVER","STORM","TRAIL"
        ]
        for w in seed:
            if not db.query(Word).filter(Word.text == w).first():
                db.add(Word(text=w))
        db.commit()
    finally:
        db.close()

# -----------------------
# Auth dependency
# -----------------------
def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.username == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# -----------------------
# Endpoints
# -----------------------
@app.post("/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if len(payload.username) < 5 or not any(c.islower() for c in payload.username) or not any(c.isupper() for c in payload.username):
        raise HTTPException(status_code=400, detail="Username must have at least 5 letters with both lower and upper case")
    pw = payload.password
    if len(pw) < 5 or not any(c.isalpha() for c in pw) or not any(c.isdigit() for c in pw) or not any(c in "$%*@" for c in pw):
        raise HTTPException(status_code=400, detail="Password must be min 5 chars and include letter, number and one of $ % * @")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(username=payload.username, password_hash=hash_password(payload.password), is_admin=bool(payload.is_admin))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"msg": "registered"}

@app.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"sub": user.username, "is_admin": user.is_admin})
    return {"access_token": token, "token_type": "bearer", "username": user.username, "role": ("admin" if user.is_admin else "player")}

@app.post("/start_game", response_model=StartGameOut)
def start_game(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    games_today = db.query(Game).filter(Game.user_id == user.id, func.date(Game.started_at) == today).count()
    if games_today >= 3:
        raise HTTPException(status_code=403, detail="Max 3 games per day")
    word = db.query(Word).order_by(func.random()).first()
    if not word:
        raise HTTPException(status_code=500, detail="No words available")
    game = Game(user_id=user.id, word_id=word.id)
    db.add(game)
    db.commit()
    db.refresh(game)
    return {"game_id": game.id}

@app.post("/guess", response_model=GuessOut)
def submit_guess(payload: GuessIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == payload.game_id, Game.user_id == user.id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if not game.is_active:
        raise HTTPException(status_code=400, detail="Game not active")
    if game.attempts >= 5:
        game.is_active = False
        db.commit()
        raise HTTPException(status_code=400, detail="Max attempts reached")

    guess_text = payload.guess.upper()
    if len(guess_text) != 5 or not guess_text.isalpha():
        raise HTTPException(status_code=400, detail="Guess must be 5 letters A-Z")

    secret = db.query(Word).filter(Word.id == game.word_id).first().text
    feedback = evaluate_guess(secret, guess_text)
    guess_row = Guess(game_id=game.id, guess_text=guess_text, feedback=",".join(feedback))
    db.add(guess_row)
    game.attempts += 1

    if guess_text == secret:
        game.is_active = False
        game.is_won = True
    elif game.attempts >= 5:
        game.is_active = False

    db.commit()
    db.refresh(game)

    return {"feedback": feedback, "attempts": game.attempts, "is_won": game.is_won, "is_active": game.is_active}

@app.get("/report/daily")
def report_daily(date_str: Optional[str] = Query(None), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    if date_str:
        try:
            qdate = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            raise HTTPException(status_code=400, detail="Bad date format, use YYYY-MM-DD")
    else:
        qdate = date.today()
    users_count = db.query(func.count(func.distinct(Game.user_id))).filter(func.date(Game.started_at) == qdate).scalar()
    correct_count = db.query(func.count(Game.id)).filter(func.date(Game.started_at) == qdate, Game.is_won == True).scalar()
    return {"date": str(qdate), "users_played": users_count, "correct_guesses": correct_count}

@app.get("/report/user/{username}")
def report_user(username: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    target = db.query(User).filter(User.username == username).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    rows = db.query(Game.started_at, func.count(Game.id).label("words_tried"),
                    func.sum(func.case((Game.is_won == True, 1), else_=0)).label("correct")) \
             .filter(Game.user_id == target.id).group_by(func.date(Game.started_at)).all()
    result = [{"date": started_at.date().isoformat(), "words_tried": words_tried, "correct_guesses": int(correct or 0)} for started_at, words_tried, correct in rows]
    return {"username": username, "report": result}

# -----------------------
# Serve frontend
# -----------------------
@app.get("/")
def serve_home():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend index not found")

@app.get("/play")
def serve_play():
    game_path = os.path.join(FRONTEND_DIR, "game.html")
    if os.path.exists(game_path):
        return FileResponse(game_path)
    raise HTTPException(status_code=404, detail="Frontend game not found")

@app.get("/admin")
def serve_admin():
    admin_path = os.path.join(FRONTEND_DIR, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    raise HTTPException(status_code=404, detail="Frontend admin not found")
