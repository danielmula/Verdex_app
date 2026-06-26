"""
Validacion del initData que envia la Mini App de Telegram.

Telegram firma los datos del usuario con un hash basado en el token del bot.
Validarlo evita que alguien llame a tu API por fuera de Telegram (clave para
controlar suscripciones / premium).

Docs: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

import hashlib
import hmac
import os
from urllib.parse import parse_qsl
import json

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")


def validate_init_data(init_data: str) -> dict | None:
    """
    Devuelve el dict con los datos del usuario si la firma es valida,
    o None si no lo es. Si no hay BOT_TOKEN configurado, en modo desarrollo
    devuelve un usuario falso para poder probar la Mini App en el navegador.
    """
    if not init_data:
        # Modo desarrollo: sin Telegram, devolvemos usuario de prueba
        if os.environ.get("USE_MOCK", "true").lower() == "true":
            return {"id": 0, "first_name": "Dev", "username": "dev"}
        return None

    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    # Construir la data_check_string ordenada alfabeticamente
    data_check = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(
        b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256
    ).digest()
    computed_hash = hmac.new(
        secret_key, data_check.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    user_raw = parsed.get("user")
    if not user_raw:
        return None
    try:
        return json.loads(user_raw)
    except json.JSONDecodeError:
        return None
