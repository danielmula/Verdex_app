"""
Backend principal: API + sirve la Mini App.

Endpoints:
  GET  /                      -> sirve la Mini App (index.html)
  GET  /api/matches?date=     -> partidos del dia agrupados por liga
  GET  /api/match/{id}        -> stats de un partido (campos premium ocultos si no premium)
  POST /api/analysis          -> analisis con ChatGPT (premium)
  POST /api/pay               -> crea cobro Kunfupay (devuelve pay_url)
  POST /webhook/kunfupay      -> Kunfupay nos avisa cuando alguien paga
  GET  /api/me                -> dice si el usuario es premium
"""

import os
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import footystats, analysis, subscriptions
from .telegram_auth import validate_init_data

app = FastAPI(title="Botanalist Mini App")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _user_from_header(x_init_data: str | None) -> dict:
    user = validate_init_data(x_init_data or "")
    if user is None:
        raise HTTPException(status_code=401, detail="initData invalido")
    return user


@app.get("/")
async def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/me")
async def me(x_init_data: str | None = Header(default=None)):
    user = _user_from_header(x_init_data)
    return {"user_id": user["id"], "premium": subscriptions.is_premium(user["id"])}


@app.get("/api/matches")
async def matches(date: str | None = None,
                  x_init_data: str | None = Header(default=None)):
    _user_from_header(x_init_data)
    items = await footystats.get_todays_matches(date)
    # Agrupar por liga para el desplegable / secciones
    leagues: dict[str, dict] = {}
    for m in items:
        key = m["league"]
        leagues.setdefault(key, {
            "league": key, "country": m["country"], "matches": []
        })
        leagues[key]["matches"].append(m)
    return {
        "date": date,
        "leagues": list(leagues.values()),
        "all_leagues": sorted(leagues.keys()),
    }


@app.get("/api/match/{match_id}")
async def match_detail(match_id: int,
                       x_init_data: str | None = Header(default=None)):
    user = _user_from_header(x_init_data)
    data = await footystats.get_match_stats(match_id)
    if not data:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    premium = subscriptions.is_premium(user["id"])
    data["premium_user"] = premium
    # El General se ve gratis; goles/corners/tarjetas avanzado = premium
    # (la Mini App muestra el muro de pago segun este flag)
    return data


class AnalysisIn(BaseModel):
    match_id: int
    question: str


@app.post("/api/analysis")
async def do_analysis(body: AnalysisIn,
                      x_init_data: str | None = Header(default=None)):
    user = _user_from_header(x_init_data)
    if not subscriptions.is_premium(user["id"]):
        raise HTTPException(status_code=402, detail="Funcion premium")
    match = await footystats.get_match_stats(body.match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    text = await analysis.analyze_match(match, body.question)
    return {"analysis": text}


class PayIn(BaseModel):
    plan: str  # 'subscription' | 'deposit'


@app.post("/api/pay")
async def pay(body: PayIn, x_init_data: str | None = Header(default=None)):
    user = _user_from_header(x_init_data)
    result = await subscriptions.create_payment(user["id"], body.plan)
    return result


@app.post("/webhook/kunfupay")
async def kunfupay_webhook(request: Request):
    """
    Kunfupay llama aqui cuando alguien paga. PENDIENTE: verificar la firma
    del webhook segun su doc. De momento leemos user_id y damos premium.
    """
    payload = await request.json()
    # TODO: verificar firma/secret de Kunfupay antes de confiar en esto
    user_id = payload.get("metadata", {}).get("user_id")
    if user_id is not None:
        subscriptions.grant_premium(int(user_id))
        return {"ok": True}
    raise HTTPException(status_code=400, detail="Falta user_id")


@app.get("/health")
async def health():
    return {"status": "ok"}
