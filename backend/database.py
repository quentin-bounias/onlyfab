from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# Le fichier SQLite sera dans le dossier /data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'onlyfab.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # nécessaire pour SQLite + FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dépendance FastAPI : ouvre et ferme la session automatiquement
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
