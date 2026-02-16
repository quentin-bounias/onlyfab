from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    filename = Column(String, nullable=False, unique=True)  # nom du fichier dans /media
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Votes où cette personne était à gauche ou à droite
    votes_as_winner = relationship(
        "Vote", foreign_keys="Vote.winner_id", back_populates="winner"
    )
    votes_as_loser = relationship(
        "Vote", foreign_keys="Vote.loser_id", back_populates="loser"
    )


class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    winner_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    loser_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    voter_ip = Column(String, nullable=False)  # anti-bourrage
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    winner = relationship(
        "Person", foreign_keys=[winner_id], back_populates="votes_as_winner"
    )
    loser = relationship(
        "Person", foreign_keys=[loser_id], back_populates="votes_as_loser"
    )
