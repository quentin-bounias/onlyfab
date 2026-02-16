# Image de base Python 3.11 slim
FROM python:3.11-slim

# Dépendances système pour Pillow
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# Répertoire de travail
WORKDIR /app

# Installe les dépendances Python en premier
# (layer Docker mis en cache tant que requirements.txt ne change pas)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie le code backend
COPY backend/ ./backend/

# Copie le frontend
COPY frontend/ ./frontend/

# Crée les dossiers de données au build
RUN mkdir -p /app/media /app/data

# Exposition du port
EXPOSE 8042

# Démarrage avec uvicorn
CMD ["uvicorn", "backend.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8042", \
     "--workers", "2"]