# 📰 Agrégateur RSS — Veille politique française

Résumé **hebdomadaire automatisé** de la vie politique française (Assemblée nationale + Sénat), généré par IA et envoyé par email. Pensé pour un lecteur **débutant** souhaitant progresser dans la compréhension des enjeux politiques et sociaux du pays.

Chaque édition contient :

- **Résumé de la semaine** — 5 à 7 points factuels sur les textes débattus et adoptés ;
- **Débat principal** — l'événement le plus marquant, expliqué simplement ;
- **Contexte historique** — quelques puces retraçant l'histoire du sujet et les **partis politiques impliqués**, pour la culture générale.

---

## ⚙️ Fonctionnement

1. **Récupération** (`fetcher.py`) — agrège plusieurs flux RSS officiels de l'Assemblée nationale et du Sénat sur les 7 derniers jours.
2. **Synthèse** (`summarizer.py`) — envoie les articles à l'API **Mistral**, qui renvoie un résumé structuré (JSON).
3. **Mise en forme** (`templates/email.html`) — rend un email HTML responsive via Jinja2.
4. **Envoi** (`mailer.py`) — expédie l'email via SMTP Gmail.

Le tout est orchestré par `main.py` et planifié via **cron** sur un serveur Linux.

## 📁 Structure du projet

| Fichier | Rôle |
|---|---|
| `main.py` | Point d'entrée et orchestration (modes `--rss-only`, `--dry-run`, complet) |
| `config.py` | Chargement des variables d'environnement (`.env`) |
| `fetcher.py` | Récupération et agrégation des flux RSS |
| `summarizer.py` | Génération du résumé via l'API Mistral |
| `mailer.py` | Envoi de l'email (SMTP Gmail) |
| `templates/email.html` | Gabarit HTML de l'email |
| `requirements.txt` | Dépendances Python |
| `.env` | Secrets — **non versionné** |

## 📋 Prérequis

- Python 3.9 ou supérieur
- Une clé API **Mistral** — <https://console.mistral.ai>
- Un compte **Gmail** avec un **mot de passe d'application** (validation en 2 étapes activée)

## 🚀 Installation (local)

```bash
git clone https://github.com/Dereckt374/agregateur_rss_vie_politique.git
cd agregateur_rss_vie_politique

python -m venv .venv
# Windows :        .venv\Scripts\activate
# Linux / macOS :  source .venv/bin/activate

pip install -r requirements.txt
```

Puis copier le modèle d'environnement et le compléter :

```bash
cp .env.example .env   # puis éditer .env avec vos valeurs
```

## 🔑 Configuration (`.env`)

| Variable | Requis | Description |
|---|:---:|---|
| `MISTRAL_API_KEY` | ✅ | Clé API Mistral |
| `MISTRAL_MODEL` | ❌ | Modèle Mistral (défaut : `mistral-small-latest`) |
| `SMTP_USER` | ✅ * | Adresse Gmail d'envoi |
| `SMTP_PASSWORD` | ✅ * | Mot de passe d'application Gmail (16 caractères) |
| `EMAIL_FROM` | ❌ | Expéditeur affiché (défaut : `SMTP_USER`) |
| `EMAIL_TO` | ✅ * | Destinataire du résumé |

\* Requis uniquement pour l'envoi réel (inutile en `--dry-run` / `--rss-only`).

> **Mot de passe d'application Gmail** : Compte Google → *Sécurité* → *Validation en 2 étapes* → *Mots de passe des applications*.

## ▶️ Utilisation

| Commande | Effet | Clés requises |
|---|---|---|
| `python main.py --rss-only` | Affiche les flux RSS récupérés | Aucune |
| `python main.py --dry-run` | Génère `output/preview.html` (sans email) | Mistral |
| `python main.py` | Pipeline complet + envoi de l'email | Mistral + Gmail |

> Le mode `--dry-run` est idéal pour itérer sur le rendu ou le prompt sans envoyer d'email.

## 📡 Flux RSS suivis

**Assemblée nationale**
- Communiqués de presse
- Comptes-rendus des débats
- Commission des Finances
- Commission des Lois
- Commission des Affaires sociales

**Sénat**
- Communiqués de presse
- Textes législatifs
- Rapports

## 🖥️ Déploiement (VPS Linux + cron)

```bash
# Prérequis système (Debian/Ubuntu ; pour RHEL : sudo dnf install -y python3 python3-pip git)
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git

# Récupération du projet
cd ~
git clone https://github.com/Dereckt374/agregateur_rss_vie_politique.git
cd agregateur_rss_vie_politique

# Environnement + dépendances
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Secrets (jamais via git)
nano .env
```

Planifier l'exécution (quotidienne à 08h00) :

```bash
cd ~/agregateur_rss_vie_politique
APP_DIR="$PWD"
( crontab -l 2>/dev/null; echo "0 8 * * * cd $APP_DIR && $APP_DIR/.venv/bin/python main.py >> $APP_DIR/cron.log 2>&1" ) | crontab -
crontab -l   # vérifier
```

- **Hebdomadaire** (dimanche 8h) : remplacer `0 8 * * *` par `0 8 * * 0`.
- **Fuseau horaire** : `sudo timedatectl set-timezone Europe/Paris`.
- **Logs** : `cat ~/agregateur_rss_vie_politique/cron.log`.

## 🎨 Personnalisation

- **Période couverte** — paramètre `days` dans `fetch_items(...)` (`main.py`).
- **Ton et structure du résumé** — prompt `_PROMPT` dans `summarizer.py`.
- **Apparence de l'email** — `templates/email.html`.
- **Flux RSS** — liste des flux dans `fetcher.py`.

## ⚠️ Pièges connus

- **`mistralai` doit rester en version 1.x** (`mistralai>=1.0.0,<2.0.0`). La v2.x s'installe comme « namespace package » sans `__init__.py` et provoque `ImportError: cannot import name 'Mistral'`.
- Sur Windows, la console (cp1252) peut afficher des accents abîmés ; les fichiers HTML restent en UTF-8 correct. Définir `PYTHONIOENCODING=utf-8` pour des logs propres.
