FROM python:3.10-slim

# Définir le dossier de travail
WORKDIR /app

# Copier les dépendances
COPY . /app

# Définir l'environnement

RUN pip install --no-cache-dir -r requirements.txt

# Commande par défaut pour exécuter le script Python
CMD ["python", "fichier_.py"]
