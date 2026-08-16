FROM python:3.11-slim

# variables build
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8050

# installer dépendances système nécessaires pour geopandas/fiona/shapely
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Indiquer où chercher les headers GDAL (optionnel selon image)
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# répertoire de travail
WORKDIR /app

# copier dépendances
COPY requirements.txt /app/requirements.txt

# installer dépendances Python
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /app/requirements.txt

# copier le code
COPY . /app

# Exposer le port
EXPOSE ${PORT}

# Commande de démarrage (Gunicorn + le serveur Flask de Dash)
# 'app:server' => module app.py, objet Flask app.server fourni par Dash
CMD ["gunicorn", "app:server", "--bind", "0.0.0.0:8050", "--workers", "4", "--threads", "2"]
