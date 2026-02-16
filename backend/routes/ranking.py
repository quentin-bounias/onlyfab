from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from backend.database import get_db
from backend.models import Person, Vote
from backend.schemas import RankedPerson
from typing import Literal

router = APIRouter(prefix="/api/ranking", tags=["ranking"])

PERIOD = Literal["day", "week", "month", "year"]

INITIAL_ELO = 1000.0
K_FACTOR = 32.0


def get_period_start(period: PERIOD) -> datetime:
    """Retourne le début de la période en UTC."""
    now = datetime.now(timezone.utc)
    if period == "day":
        return now - timedelta(days=1)
    elif period == "week":
        return now - timedelta(weeks=1)
    elif period == "month":
        return now - timedelta(days=30)
    elif period == "year":
        return now - timedelta(days=365)


def compute_elo(persons: list[Person], votes: list[Vote]) -> dict[int, float]:
    """
    Calcule les scores Elo à partir de zéro pour une liste de votes.
    Tous les joueurs partent à 1000. Les votes sont rejoués dans l'ordre chronologique.
    """
    scores = {p.id: INITIAL_ELO for p in persons}

    # Trie les votes du plus ancien au plus récent
    sorted_votes = sorted(votes, key=lambda v: v.created_at)

    for vote in sorted_votes:
        w_id = vote.winner_id
        l_id = vote.loser_id

        # Ignore si un des deux candidats n'est plus en base
        if w_id not in scores or l_id not in scores:
            continue

        elo_w = scores[w_id]
        elo_l = scores[l_id]

        # Probabilité attendue de victoire
        expected_w = 1 / (1 + 10 ** ((elo_l - elo_w) / 400))
        expected_l = 1 - expected_w

        # Mise à jour des scores
        scores[w_id] = elo_w + K_FACTOR * (1 - expected_w)
        scores[l_id] = elo_l + K_FACTOR * (0 - expected_l)

    return scores


@router.get("/{period}", response_model=list[RankedPerson])
def get_ranking(period: PERIOD, db: Session = Depends(get_db)):
    """Retourne le classement Elo pour la période demandée."""

    if period not in ("day", "week", "month", "year"):
        raise HTTPException(status_code=400, detail="Période invalide.")

    since = get_period_start(period)

    # Votes de la période
    votes = db.query(Vote).filter(Vote.created_at >= since).all()

    if not votes:
        return []

    # Uniquement les personnes impliquées dans ces votes
    person_ids = set()
    for v in votes:
        person_ids.add(v.winner_id)
        person_ids.add(v.loser_id)

    persons = db.query(Person).filter(Person.id.in_(person_ids)).all()

    # Calcul Elo
    scores = compute_elo(persons, votes)

    # Stats wins/losses par personne
    wins = {p.id: 0 for p in persons}
    losses = {p.id: 0 for p in persons}
    for v in votes:
        if v.winner_id in wins:
            wins[v.winner_id] += 1
        if v.loser_id in losses:
            losses[v.loser_id] += 1

    # Construction du classement trié par score décroissant
    ranked = []
    for rank, person in enumerate(
        sorted(persons, key=lambda p: scores[p.id], reverse=True), start=1
    ):
        ranked.append(
            RankedPerson(
                rank=rank,
                person=person,
                elo=round(scores[person.id], 1),
                wins=wins[person.id],
                losses=losses[person.id],
                games=wins[person.id] + losses[person.id],
            )
        )

    return ranked
