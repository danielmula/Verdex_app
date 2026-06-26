"""
Analisis del partido en lenguaje natural usando la API de OpenAI (ChatGPT).

Recibe las stats del partido + la pregunta del usuario y devuelve un analisis
en español. Requiere OPENAI_API_KEY en las variables de entorno.

Si no hay key, devuelve un mensaje mock para que puedas probar el flujo.
"""

import os
import httpx

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = (
    "Eres un analista deportivo experto en estadistica de futbol. "
    "Te paso las estadisticas de un partido y una pregunta del usuario. "
    "Da un analisis claro, conciso y honesto en español, basado SOLO en los "
    "datos proporcionados. No inventes datos. No garantices resultados ni "
    "animes a apostar dinero: explica probabilidades y tendencias de forma "
    "informativa. Si los datos no permiten responder, dilo."
)


def _build_context(match: dict) -> str:
    s = match.get("stats", {})
    return (
        f"Partido: {match.get('home')} vs {match.get('away')}\n"
        f"Liga: {match.get('league')} ({match.get('country')})\n"
        f"Forma local: {'-'.join(match.get('home_form', []))}\n"
        f"Forma visitante: {'-'.join(match.get('away_form', []))}\n"
        f"Mas de 2.5 goles: {s.get('over_25')}% (media liga {s.get('over_25_league')}%)\n"
        f"Mas de 1.5 goles: {s.get('over_15')}% (media liga {s.get('over_15_league')}%)\n"
        f"Ambos marcan (BTTS): {s.get('btts')}% (media liga {s.get('btts_league')}%)\n"
        f"Goles por partido: {s.get('goals_avg')} (media liga {s.get('goals_avg_league')})\n"
        f"Tarjetas: {s.get('cards_avg')} (media liga {s.get('cards_avg_league')})\n"
        f"Corners: {s.get('corners_avg')} (media liga {s.get('corners_avg_league')})\n"
    )


async def analyze_match(match: dict, question: str) -> str:
    context = _build_context(match)

    if not OPENAI_API_KEY:
        return (
            "[Modo demo · sin OPENAI_API_KEY]\n\n"
            f"Análisis de {match.get('home')} vs {match.get('away')}:\n"
            "Cuando configures tu OPENAI_API_KEY en Render, aquí aparecerá el "
            "análisis real generado por ChatGPT a partir de estas estadísticas:\n\n"
            f"{context}"
        )

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{context}\nPregunta del usuario: {question}"},
        ],
        "temperature": 0.4,
        "max_tokens": 500,
    }
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    async with httpx.AsyncClient(timeout=40) as client:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload, headers=headers,
        )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
