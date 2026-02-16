from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Person
from backend.schemas import PersonOut
from backend.utils.image import process_image, get_media_path
import os
import secrets
import uuid

router = APIRouter(prefix="/api/admin", tags=["admin"])
security = HTTPBasic()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Vérifie le login/mot de passe admin via variables d'environnement."""
    correct_username = os.environ.get("ADMIN_USER", "admin")
    correct_password = os.environ.get("ADMIN_PASSWORD", "changeme")

    username_ok = secrets.compare_digest(credentials.username, correct_username)
    password_ok = secrets.compare_digest(credentials.password, correct_password)

    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=401,
            detail="Identifiants incorrects.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@router.get("/persons", response_model=list[PersonOut])
def list_persons(db: Session = Depends(get_db), _: str = Depends(verify_admin)):
    """Liste tous les candidats."""
    return db.query(Person).order_by(Person.created_at.desc()).all()


@router.post("/persons", response_model=PersonOut)
async def add_person(
    name: str = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin),
):
    """Ajoute un candidat avec sa photo (tous formats acceptés)."""

    # Extension forcée en .jpg après traitement
    unique_filename = f"{uuid.uuid4().hex}.jpg"
    tmp_path = f"/tmp/{uuid.uuid4().hex}_original"
    output_path = get_media_path(BASE_DIR, unique_filename)

    # Sauvegarde temporaire du fichier uploadé
    content = await photo.read()
    with open(tmp_path, "wb") as f:
        f.write(content)

    # Traitement image : crop + resize + compression
    try:
        process_image(tmp_path, output_path)
    except Exception as e:
        os.remove(tmp_path)
        raise HTTPException(
            status_code=422, detail=f"Erreur traitement image : {str(e)}"
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    # Enregistrement en base
    person = Person(name=name, filename=unique_filename)
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@router.delete("/persons/{person_id}")
def delete_person(
    person_id: int, db: Session = Depends(get_db), _: str = Depends(verify_admin)
):
    """Supprime un candidat et sa photo."""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Candidat introuvable.")

    # Suppression du fichier image
    media_path = get_media_path(BASE_DIR, person.filename)
    if os.path.exists(media_path):
        os.remove(media_path)

    db.delete(person)
    db.commit()
    return {"message": f"{person.name} supprimé avec succès."}
