from pydantic import BaseModel, constr
from typing import List

class RegisterIn(BaseModel):
    username: str
    password: str

class LoginIn(BaseModel):
    username: str
    password: str

class StartGameOut(BaseModel):
    game_id: int

class GuessIn(BaseModel):
    game_id: int
    guess: constr(min_length=5, max_length=5)

class GuessOut(BaseModel):
    feedback: List[str]
    attempts: int
    is_won: bool
    is_active: bool
