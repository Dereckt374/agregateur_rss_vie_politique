#!/usr/bin/env python3
"""Point d'entrée principal du résumé hebdomadaire de vie politique française.

Modes d'exécution :
  python main.py              → tout : RSS + résumé Mistral + envoi email
  python main.py --dry-run    → RSS + résumé Mistral, écrit le HTML dans output/ (pas d'email)
  python main.py --rss-only   → récupère et affiche les flux RSS seuls (aucune clé requise)
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from config import load_config
from fetcher import fetch_items, format_for_prompt
# summarizer (mistralai) et mailer (smtp) sont importés paresseusement dans main(),
# pour que --rss-only fonctionne sans aucune clé ni dépendance IA.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"


def render_html(summary, date_debut: str, date_fin: str) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    template = env.get_template("email.html")
    return template.render(
        date_debut=date_debut,
        date_fin=date_fin,
        resume_semaine=summary.resume_semaine,
        evenement_titre=summary.evenement_titre,
        evenement_description=summary.evenement_description,
        evenement_contexte=summary.evenement_contexte,
    )


def run_rss_only() -> None:
    logger.info("Mode --rss-only : récupération des flux (aucune clé requise)…")
    items = fetch_items(days=7)
    if not items:
        logger.error("Aucun article récupéré. Vérifiez la connectivité réseau.")
        sys.exit(1)
    logger.info("%d article(s) récupéré(s) sur les 7 derniers jours :\n", len(items))
    print(format_for_prompt(items))


def main() -> None:
    parser = argparse.ArgumentParser(description="Veille politique française hebdomadaire")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Génère le HTML dans output/ sans envoyer d'email (clé Mistral requise, Gmail non).",
    )
    parser.add_argument(
        "--rss-only",
        action="store_true",
        help="Affiche seulement les flux RSS récupérés (aucune clé requise).",
    )
    args = parser.parse_args()

    if args.rss_only:
        run_rss_only()
        return

    config = load_config(require_smtp=not args.dry_run)

    now = datetime.now(timezone.utc)
    date_fin = now.strftime("%d/%m/%Y")
    date_debut = (now - timedelta(days=7)).strftime("%d/%m/%Y")

    logger.info("Récupération des flux RSS (7 derniers jours)…")
    items = fetch_items(days=7)
    if not items:
        logger.error("Aucun article récupéré. Vérifiez la connectivité réseau.")
        sys.exit(1)
    logger.info("%d article(s) récupéré(s).", len(items))

    articles_text = format_for_prompt(items)

    from summarizer import generate_summary

    logger.info("Génération du résumé avec Mistral (%s)…", config.mistral_model)
    summary = generate_summary(config, articles_text, date_debut, date_fin)

    html_body = render_html(summary, date_debut, date_fin)

    if args.dry_run:
        OUTPUT_DIR.mkdir(exist_ok=True)
        out_path = OUTPUT_DIR / "preview.html"
        out_path.write_text(html_body, encoding="utf-8")
        logger.info("Mode --dry-run : email NON envoyé.")
        logger.info("Aperçu écrit dans : %s", out_path)
        logger.info("Ouvrez ce fichier dans votre navigateur pour vérifier le rendu.")
        return

    from mailer import send_email

    subject = f"Veille politique française — semaine du {date_debut} au {date_fin}"
    send_email(config, subject, html_body)


if __name__ == "__main__":
    main()
