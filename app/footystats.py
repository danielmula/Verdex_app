"""
Cliente de FootyStats con cache en memoria y modo mock.

Mientras no tengas la API key real, USE_MOCK=true devuelve datos de ejemplo
con la MISMA forma que la API real. Cuando consigas la key:
  1. Pon FOOTYSTATS_API_KEY en las variables de entorno de Render
  2. Pon USE_MOCK=false
y todo funciona con datos reales sin tocar el resto del codigo.

Docs API: https://footystats.org/api/
"""

import os
import time
import httpx

API_BASE = "https://api.football-data-api.com"
API_KEY = os.environ.get("FOOTYSTATS_API_KEY", "")
USE_MOCK = os.environ.get("USE_MOCK", "true").lower() == "true"

# Cache simple en memoria: { clave: (timestamp, datos) }
_cache: dict[str, tuple[float, object]] = {}
CACHE_TTL = int(os.environ.get("CACHE_TTL", "600"))  # 10 min por defecto


def _cache_get(key: str):
    item = _cache.get(key)
    if not item:
        return None
    ts, data = item
    if time.time() - ts > CACHE_TTL:
        _cache.pop(key, None)
        return None
    return data


def _cache_set(key: str, data: object):
    _cache[key] = (time.time(), data)


async def _get(path: str, params: dict) -> dict:
    """Llamada GET a FootyStats con la API key inyectada."""
    params = {**params, "key": API_KEY}
    url = f"{API_BASE}{path}"
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()


# ---------------------------------------------------------------------------
# Funciones publicas que usa el backend. Cada una decide mock vs real.
# ---------------------------------------------------------------------------

async def get_todays_matches(date: str | None = None) -> list[dict]:
    """Partidos de un dia. date en formato YYYY-MM-DD. None = hoy."""
    cache_key = f"matches:{date or 'today'}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    if USE_MOCK:
        data = _mock_matches(date)
    else:
        params = {}
        if date:
            params["date"] = date
        raw = await _get("/todays-matches", params)
        data = _normalize_matches(raw.get("data", []))

    _cache_set(cache_key, data)
    return data


async def get_match_stats(match_id: int) -> dict | None:
    """Estadisticas detalladas de un partido por su id."""
    cache_key = f"match:{match_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    if USE_MOCK:
        data = _mock_match_stats(match_id)
    else:
        raw = await _get("/match", {"match_id": match_id})
        data = _normalize_match_detail(raw.get("data", {}))

    _cache_set(cache_key, data)
    return data


# ---------------------------------------------------------------------------
# Normalizadores: convierten la respuesta de FootyStats a NUESTRA forma.
# Ajusta los nombres de campo segun lo que devuelva tu plan real.
# ---------------------------------------------------------------------------

def _normalize_matches(raw_list: list[dict]) -> list[dict]:
    out = []
    for m in raw_list:
        out.append({
            "id": m.get("id"),
            "league": m.get("competition_name") or m.get("league_name", "—"),
            "country": m.get("country", ""),
            "home": m.get("home_name", "?"),
            "away": m.get("away_name", "?"),
            "home_flag": m.get("home_image", ""),
            "away_flag": m.get("away_image", ""),
            "time": _to_hhmm(m.get("date_unix")),
            "status": _status_label(m.get("status", "")),
        })
    return out


def _normalize_match_detail(m: dict) -> dict:
    return {
        "id": m.get("id"),
        "league": m.get("competition_name", "—"),
        "country": m.get("country", ""),
        "home": m.get("home_name", "?"),
        "away": m.get("away_name", "?"),
        "home_flag": m.get("home_image", ""),
        "away_flag": m.get("away_image", ""),
        "time": _to_hhmm(m.get("date_unix")),
        "stadium": m.get("stadium_name", ""),
        "home_form": _form_list(m.get("home_recent", "")),
        "away_form": _form_list(m.get("away_recent", "")),
        "stats": {
            "over_25": m.get("o25_potential"),
            "over_15": m.get("o15_potential"),
            "btts": m.get("btts_potential"),
            "goals_avg": m.get("avg_potential"),
            "cards_avg": m.get("cards_potential"),
            "corners_avg": m.get("corners_potential"),
        },
    }


def _to_hhmm(unix_ts) -> str:
    if not unix_ts:
        return "--:--"
    t = time.localtime(int(unix_ts))
    return f"{t.tm_hour:02d}:{t.tm_min:02d}"


def _status_label(status: str) -> str:
    mapping = {"complete": "FT", "incomplete": "—", "suspended": "SUSP"}
    return mapping.get(status, status or "—")


def _form_list(s: str) -> list[str]:
    # FootyStats suele dar algo como "WLDWW"
    return [c for c in (s or "") if c in "WLD"][:5]


# ---------------------------------------------------------------------------
# DATOS MOCK (forma identica a lo que devuelven las funciones de arriba)
# ---------------------------------------------------------------------------

def _mock_matches(date: str | None) -> list[dict]:
    return [
        {"id": 1001, "league": "World Cup", "country": "World",
         "home": "Paraguay", "away": "Australia",
         "home_flag": "https://flagcdn.com/w80/py.png",
         "away_flag": "https://flagcdn.com/w80/au.png",
         "time": "04:00", "status": "FT"},
        {"id": 1002, "league": "World Cup", "country": "World",
         "home": "Türkiye", "away": "USA",
         "home_flag": "https://flagcdn.com/w80/tr.png",
         "away_flag": "https://flagcdn.com/w80/us.png",
         "time": "04:00", "status": "FT"},
        {"id": 1003, "league": "World Cup", "country": "World",
         "home": "Norway", "away": "France",
         "home_flag": "https://flagcdn.com/w80/no.png",
         "away_flag": "https://flagcdn.com/w80/fr.png",
         "time": "21:00", "status": "1H"},
        {"id": 1004, "league": "World Cup", "country": "World",
         "home": "Senegal", "away": "Iraq",
         "home_flag": "https://flagcdn.com/w80/sn.png",
         "away_flag": "https://flagcdn.com/w80/iq.png",
         "time": "21:00", "status": "1H"},
        {"id": 2001, "league": "LaLiga", "country": "Spain",
         "home": "Rayo Vallecano", "away": "Strasbourg",
         "home_flag": "https://flagcdn.com/w80/es.png",
         "away_flag": "https://flagcdn.com/w80/fr.png",
         "time": "18:30", "status": "—"},
        {"id": 2002, "league": "Premier League", "country": "England",
         "home": "Shakhtar Donetsk", "away": "Crystal Palace",
         "home_flag": "https://flagcdn.com/w80/ua.png",
         "away_flag": "https://flagcdn.com/w80/gb-eng.png",
         "time": "20:00", "status": "—"},
        {"id": 2003, "league": "Primeira Liga", "country": "Portugal",
         "home": "SC Braga", "away": "SC Freiburg",
         "home_flag": "https://flagcdn.com/w80/pt.png",
         "away_flag": "https://flagcdn.com/w80/de.png",
         "time": "21:00", "status": "—"},
    ]


def _mock_match_stats(match_id: int) -> dict:
    base = {m["id"]: m for m in _mock_matches(None)}
    m = base.get(match_id, base[1002])
    return {
        "id": m["id"],
        "league": m["league"],
        "country": m["country"],
        "home": m["home"],
        "away": m["away"],
        "home_flag": m["home_flag"],
        "away_flag": m["away_flag"],
        "time": m["time"],
        "stadium": "SoFi Stadium",
        "home_form": ["W", "L", "L", "W", "W"],
        "away_form": ["L", "W", "W", "L", "W"],
        "stats": {
            "over_25": 59, "over_25_league": 60.28,
            "over_15": 79, "over_15_league": 76.28,
            "btts": 56, "btts_league": 54.08,
            "goals_avg": 3.2, "goals_avg_league": 2.85,
            "cards_avg": 3.94, "cards_avg_league": 4.85,
            "corners_avg": 10.15, "corners_avg_league": 8.96,
        },
    }
