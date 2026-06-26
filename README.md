# Botanalist — Bot de Telegram + Mini App de estadísticas

Mini App dentro de Telegram con partidos del día, ligas, estadísticas y un chat
de análisis con ChatGPT. Datos de FootyStats. Pagos con Kunfupay. Pensado para
desplegar en Render.

## Qué hace ahora mismo

- **Funciona ya con datos de ejemplo (mock)**, sin necesidad de FootyStats.
- Lista de partidos del día agrupados por liga + desplegable de ligas.
- Detalle de partido con estadísticas (estilo de las capturas).
- Muro de pago premium (TOP 3, goles, córners, tarjetas, análisis avanzado).
- Chat de análisis con ChatGPT (premium).
- Validación de `initData` de Telegram para seguridad.

## Estructura

```
app/
  main.py            API FastAPI + sirve la Mini App
  footystats.py      Cliente FootyStats (+ cache + datos mock)
  analysis.py        Análisis con ChatGPT
  subscriptions.py   Premium + placeholder Kunfupay
  telegram_auth.py   Validación de initData
  static/index.html  La Mini App (HTML/JS)
bot.py               Bot de Telegram (menu button)
render.yaml          Configuración de los 2 servicios de Render
requirements.txt
.env.example         Plantilla de variables de entorno
```

## Cómo desplegarlo (orden correcto)

### 1. Sube el código a GitHub
Crea un repo y sube esta carpeta. (`git init`, `git add .`, `git commit`, `git push`).

### 2. Despliega en Render con el Blueprint
- Entra en Render → New → **Blueprint** → conecta tu repo.
- Render leerá `render.yaml` y creará **dos servicios**:
  - `botanalist-web` → la API + Mini App
  - `botanalist-bot` → el bot
- Al crear el web service, Render te da una URL tipo
  `https://botanalist-web.onrender.com`. **Esa es tu URL.**

### 3. Pon las variables de entorno
En el panel de Render, en **cada** servicio, rellena:

**botanalist-web:**
- `TELEGRAM_BOT_TOKEN` = tu token de BotFather
- `OPENAI_API_KEY` = tu key de platform.openai.com (para el chat)
- `USE_MOCK` = `true` (cámbialo a `false` cuando tengas FootyStats)
- `FOOTYSTATS_API_KEY` = (cuando la tengas)
- `KUNFUPAY_API_KEY` / `KUNFUPAY_BASE` = (cuando integremos Kunfupay)

**botanalist-bot:**
- `TELEGRAM_BOT_TOKEN` = el mismo token
- `WEBAPP_URL` = la URL del web service (paso 2)

### 4. Listo
El bot configura solo el menu button al arrancar (mira `bot.py → post_init`).
Abre tu bot en Telegram, pulsa **Abrir App** y verás la Mini App.

## Cuando consigas la API de FootyStats
1. Pon `FOOTYSTATS_API_KEY` en `botanalist-web`.
2. Cambia `USE_MOCK` a `false`.
3. Revisa los nombres de campo en `footystats.py` (funciones `_normalize_*`)
   y ajústalos a lo que devuelva tu plan. Los endpoints usados son
   `/todays-matches` y `/match`.

## Pendiente: Kunfupay
En `subscriptions.py → create_payment()` y en `main.py → /webhook/kunfupay`
están los huecos marcados con `TODO`. Cuando tengas la documentación de
Kunfupay (si da API + webhook, o solo links de pago), se completan esos dos
puntos y el muro de pago queda 100% automático.

## Probar en local (opcional)
```
pip install -r requirements.txt
cp .env.example .env   # rellena lo que tengas
USE_MOCK=true uvicorn app.main:app --reload
```
Abre http://127.0.0.1:8000 — en modo mock entra como usuario "Dev".

## Nota sobre el plan Free de Render
El servicio web gratis "se duerme" tras inactividad y tarda unos segundos en
despertar. El estado premium se guarda en memoria, así que se borra al
reiniciar: para producción real conviene una base de datos (SQLite con disco
persistente o Postgres de Render). Está preparado para cambiarlo en
`subscriptions.py`.
