import json
import logging
from dataclasses import dataclass

from mistralai import Mistral

logger = logging.getLogger(__name__)

_PROMPT = """\
Tu es un assistant pédagogique spécialisé dans la vie politique française, \
conçu pour aider un lecteur débutant à comprendre les enjeux politiques actuels.

Voici les actualités parlementaires françaises de la semaine du {date_debut} au {date_fin}, \
issues de l'Assemblée nationale et du Sénat :

---
{articles}
---

Le lecteur est un débutant qui souhaite progresser dans la compréhension \
de la politique française. Génère un résumé structuré en JSON avec exactement ce format :

{{
  "resume_semaine": [
    "Thème ou mesure : phrase factuelle décrivant ce qui a été débattu ou adopté.",
    "..."
  ],
  "evenement_principal": {{
    "titre": "Titre court et explicite de l'événement ou débat le plus important",
    "description": "Description en 2-3 phrases accessibles expliquant de quoi il s'agit et pourquoi c'est important pour les citoyens.",
    "contexte_historique": [
      "Point historique : origine ou date clé, en précisant le parti, le gouvernement ou le ministre à l'origine de la loi citée.",
      "Point historique : évolution marquante, en précisant les partis qui ont porté ou combattu la réforme.",
      "Point historique : situation actuelle et principales lignes de clivage entre les partis."
    ]
  }}
}}

Règles :
- resume_semaine : entre 5 et 7 points, pas plus.
- Chaque point doit être factuel et autoportant : commence directement par le thème ou la mesure \
concernée (ex. « Protection de l'enfance : … », « Retraites agricoles : … »). N'utilise JAMAIS de \
verbe pédagogique en tête de point (pas de « Découvrir », « Comprendre », « Analyser », « Étudier », \
« Examiner », « S'intéresser »).
- contexte_historique : une liste de 3 à 5 puces (jamais un paragraphe). Style pédagogique et \
accessible, sans jargon.
- Dans contexte_historique, chaque fois qu'une loi, une réforme ou une décision est citée, mentionne \
explicitement le ou les partis politiques, le gouvernement ou le ministre qui l'ont portée, et le cas \
échéant ceux qui s'y sont opposés.
- Réponds UNIQUEMENT avec le JSON, sans texte avant ni après, sans balises markdown.
"""


@dataclass
class WeeklySummary:
    resume_semaine: list[str]
    evenement_titre: str
    evenement_description: str
    evenement_contexte: list[str]


def generate_summary(
    config,
    articles_text: str,
    date_debut: str,
    date_fin: str,
) -> WeeklySummary:
    client = Mistral(api_key=config.mistral_api_key)

    prompt = _PROMPT.format(
        date_debut=date_debut,
        date_fin=date_fin,
        articles=articles_text,
    )

    response = client.chat.complete(
        model=config.mistral_model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()
    logger.debug("Réponse Mistral brute : %s", raw[:200])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("JSON invalide reçu de Mistral : %s", raw[:500])
        raise RuntimeError("La réponse de Mistral n'est pas un JSON valide.") from exc

    event = data.get("evenement_principal", {})
    return WeeklySummary(
        resume_semaine=data.get("resume_semaine", []),
        evenement_titre=event.get("titre", ""),
        evenement_description=event.get("description", ""),
        evenement_contexte=event.get("contexte_historique", []),
    )
