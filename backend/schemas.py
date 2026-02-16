from pydantic import BaseModel
from datetime import datetime


# --- Person ---


class PersonBase(BaseModel):
    name: str


class PersonCreate(PersonBase):
    pass


class PersonOut(PersonBase):
    id: int
    filename: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Vote ---


class VoteCreate(BaseModel):
    winner_id: int
    loser_id: int


class VoteOut(BaseModel):
    id: int
    winner_id: int
    loser_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Paire pour le swipe ---


class Pair(BaseModel):
    left: PersonOut
    right: PersonOut


# --- Classement Elo ---


class RankedPerson(BaseModel):
    rank: int
    person: PersonOut
    elo: float
    wins: int
    losses: int
    games: int
