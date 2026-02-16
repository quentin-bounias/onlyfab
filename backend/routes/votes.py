from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from backend.database import get_db
from backend.models import Person, Vote
from backend.schemas import Pair, VoteCreate, VoteOut
import random

router = APIRouter(prefix="/api/votes", tags=["votes"])


def get_client_ip(request: Request) -> str:
    """Récupère l'IP réelle même derrière Nginx."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


@router.get("/pair", response_model=Pair)
def get_pair(db: Session = Depends(get_db)):
    """Retourne une paire aléatoire de candidats à comparer."""
    persons = db.query(Person).all()

    if len(persons) < 2:
        raise HTTPException(
            status_code=404, detail="Pas assez de candidats pour former une paire."
        )

    left, right = random.sample(persons, 2)
    return Pair(left=left, right=right)


@router.post("/", response_model=VoteOut)
def submit_vote(vote: VoteCreate, request: Request, db: Session = Depends(get_db)):
    """Enregistre un vote. Anti-bourrage : 1 vote par paire par IP toutes les 24h."""
    ip = get_client_ip(request)

    # Vérifie que les deux personnes existent
    winner = db.query(Person).filter(Person.id == vote.winner_id).first()
    loser = db.query(Person).filter(Person.id == vote.loser_id).first()

    if not winner or not loser:
        raise HTTPException(status_code=404, detail="Candidat introuvable.")

    if vote.winner_id == vote.loser_id:
        raise HTTPException(
            status_code=400, detail="Les deux candidats doivent être différents."
        )

    # Anti-bourrage : même IP, même paire, dans les 24 dernières heures
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    existing = (
        db.query(Vote)
        .filter(
            Vote.voter_ip == ip,
            Vote.created_at >= since,
            ((Vote.winner_id == vote.winner_id) & (Vote.loser_id == vote.loser_id))
            | ((Vote.winner_id == vote.loser_id) & (Vote.loser_id == vote.winner_id)),
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=429, detail="Tu as déjà voté pour cette paire aujourd'hui."
        )

    # Enregistrement du vote
    new_vote = Vote(winner_id=vote.winner_id, loser_id=vote.loser_id, voter_ip=ip)
    db.add(new_vote)
    db.commit()
    db.refresh(new_vote)
    return new_vote
