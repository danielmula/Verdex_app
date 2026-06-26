"""
Control de usuarios premium y placeholder de integracion con Kunfupay.

IMPORTANTE: ahora mismo el estado premium se guarda EN MEMORIA, asi que se
borra cada vez que Render reinicia el servicio. Para produccion real necesitas
una base de datos (SQLite en disco persistente, o Postgres en Render).
Lo dejamos preparado para cambiarlo facil.

KUNFUPAY: esta parte queda pendiente de su documentacion. Hay dos escenarios:
  A) Kunfupay tiene API + webhook  -> creamos un cobro y ellos nos avisan al
     pagar (funcion create_payment + endpoint /webhook/kunfupay en main.py)
  B) Kunfupay solo da links de pago -> generamos el link y marcamos premium
     manualmente o con un codigo. Menos automatico.
Cuando me pases los detalles de Kunfupay, completamos create_payment().
"""

import os
import time

# user_id -> timestamp de expiracion de la suscripcion
_premium: dict[int, float] = {}

SUBSCRIPTION_DAYS = int(os.environ.get("SUBSCRIPTION_DAYS", "30"))


def is_premium(user_id: int) -> bool:
    exp = _premium.get(user_id)
    if not exp:
        return False
    if time.time() > exp:
        _premium.pop(user_id, None)
        return False
    return True


def grant_premium(user_id: int, days: int = SUBSCRIPTION_DAYS):
    """Marca a un usuario como premium. Lo llamara el webhook de Kunfupay
    cuando confirme un pago."""
    _premium[user_id] = time.time() + days * 86400


# ---------------------------------------------------------------------------
# KUNFUPAY (pendiente de completar con su documentacion)
# ---------------------------------------------------------------------------

KUNFUPAY_API_KEY = os.environ.get("KUNFUPAY_API_KEY", "")
KUNFUPAY_BASE = os.environ.get("KUNFUPAY_BASE", "")


async def create_payment(user_id: int, plan: str) -> dict:
    """
    Crea un cobro en Kunfupay y devuelve { 'pay_url': ... } para redirigir
    al usuario. PENDIENTE: rellenar con los endpoints reales de Kunfupay.

    plan: 'subscription' (30 dias) o 'deposit' (primer deposito)
    """
    if not KUNFUPAY_API_KEY:
        # Placeholder mientras no tengamos la doc de Kunfupay
        return {
            "pay_url": f"https://kunfupay.example/pay?plan={plan}&uid={user_id}",
            "note": "Placeholder. Falta integrar la API real de Kunfupay.",
        }

    # TODO: cuando tengas la doc de Kunfupay, algo como:
    # async with httpx.AsyncClient() as client:
    #     r = await client.post(f"{KUNFUPAY_BASE}/charges",
    #         headers={"Authorization": f"Bearer {KUNFUPAY_API_KEY}"},
    #         json={"amount": ..., "currency": "EUR",
    #               "metadata": {"user_id": user_id, "plan": plan},
    #               "callback_url": "https://TU-APP.onrender.com/webhook/kunfupay"})
    #     return {"pay_url": r.json()["url"]}
    raise NotImplementedError("Integrar API real de Kunfupay")
