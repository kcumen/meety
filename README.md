# meety 🤖

Bot de reuniones con IA. Se une automáticamente a Google Meet / Teams / Zoom vía vexa.ai,
transcribe la reunión y genera resúmenes con tareas y compromisos usando un LLM vía OpenRouter.

## Quick start

```bash
# 1. Clonar y entrar
cd /home/Kcumen/dev/meety

# 2. Crear venv e instalar
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configurar
cp .env.example .env
# Editar .env con tus API keys

# 4. Correr
uvicorn app.main:app --reload --port 8080
```

## API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/meetings/join` | Unir bot a una reunión |
| GET | `/meetings` | Listar reuniones |
| GET | `/meetings/{platform}/{native_meeting_id}` | Detalle + resumen |
| GET | `/meetings/{platform}/{native_meeting_id}/status` | Estado del bot |
| DELETE | `/meetings/{platform}/{native_meeting_id}` | Eliminar reunión |
| POST | `/webhook/vexa` | Webhook de vexa.ai |
| GET | `/health` | Health check |

## Web UI

Abre `http://localhost:8080` en el navegador.

## Integración con Hermes

Cuando me passes una URL de reunión por Telegram, la proceso automáticamente.

## Stack

- FastAPI + Uvicorn
- SQLite + SQLAlchemy (async)
- vexa.ai (bot de reuniones)
- OpenRouter (LLM para resúmenes)
