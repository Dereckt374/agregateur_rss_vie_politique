#!/usr/bin/env bash
# Installation du projet sur le VPS et mise en place du cron hebdomadaire.
# Lancer ce script UNE SEULE FOIS depuis le dossier du projet.
# Usage : bash cron_setup.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
LOG_DIR="$PROJECT_DIR/logs"
CRON_LOG="$LOG_DIR/weekly.log"
PYTHON="$VENV_DIR/bin/python"

echo "=== Installation de la veille politique française ==="
echo "Dossier projet : $PROJECT_DIR"

# Création de l'environnement virtuel
if [ ! -d "$VENV_DIR" ]; then
  echo "Création de l'environnement virtuel Python…"
  python3 -m venv "$VENV_DIR"
fi

# Installation des dépendances
echo "Installation des dépendances Python…"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$PROJECT_DIR/requirements.txt"

# Création du dossier de logs
mkdir -p "$LOG_DIR"

# Vérification du fichier .env
if [ ! -f "$PROJECT_DIR/.env" ]; then
  echo ""
  echo "ATTENTION : Le fichier .env est manquant."
  echo "Copiez .env.example vers .env et renseignez vos clés :"
  echo "  cp $PROJECT_DIR/.env.example $PROJECT_DIR/.env"
  echo "  nano $PROJECT_DIR/.env"
  echo ""
fi

# Ajout de la tâche cron (tous les dimanches à 08h00)
CRON_JOB="0 8 * * 0 $PYTHON $PROJECT_DIR/main.py >> $CRON_LOG 2>&1"

if crontab -l 2>/dev/null | grep -qF "main.py"; then
  echo "Une entrée cron existe déjà pour ce projet. Aucune modification."
else
  (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
  echo "Tâche cron ajoutée : chaque dimanche à 08h00."
fi

echo ""
echo "=== Installation terminée ==="
echo "Logs disponibles dans : $CRON_LOG"
echo ""
echo "Pour tester immédiatement (sans attendre le cron) :"
echo "  $PYTHON $PROJECT_DIR/main.py"
