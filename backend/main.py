from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.database import Base, engine
from backend.routes import votes, ranking, admin
import os

# Création des tables au démarrage si elles n'existent pas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OnlyFab",
    description="Qui ressemble le plus à Fabien ?",
    version="1.0.0",
)

# --- Montage des routes API ---
app.include_router(votes.router)
app.include_router(ranking.router)
app.include_router(admin.router)

# --- Fichiers statiques ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Photos des candidats
app.mount(
    "/media", StaticFiles(directory=os.path.join(BASE_DIR, "media")), name="media"
)

# Assets frontend (css, js)
app.mount(
    "/static", StaticFiles(directory=os.path.join(BASE_DIR, "frontend")), name="static"
)


# --- Routes HTML ---
@app.get("/")
def serve_index():
    return FileResponse(os.path.join(BASE_DIR, "frontend", "index.html"))


@app.get("/results")
def serve_results():
    return FileResponse(os.path.join(BASE_DIR, "frontend", "results.html"))


@app.get("/admin")
def serve_admin():
    return FileResponse(os.path.join(BASE_DIR, "frontend", "admin.html"))
