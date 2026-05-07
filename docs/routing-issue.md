# Routing Issue: `GET /meetings/{id}/summary`

## Problema

El endpoint `GET /meetings/{id}/summary` (usado por la web UI para polling del resumen) devuelve consistentemente `404 Meeting not found`, incluso cuando el meeting con ese ID existe en la base de datos.

## Síntomas

- `GET /meetings/1` → 200 ✓ (encuentra el meeting id=1)
- `GET /meetings/1/summary` → 404 `{"detail":"Meeting not found"}` ✗
- `GET /meetings/google_meet/rph-iyjx-vrt/summary` → 200 ✓

## Diagnóstico

### Ruteo de FastAPI

Al inspeccionar las rutas registradas en el app:

```
10: /meetings/{meeting_id:int}/summary  name=get_meeting_summary_by_id
11: /meetings/{platform}/{native_meeting_id}/summary  name=get_meeting_summary
```

El orden sugiere que `get_meeting_summary_by_id` debería recibir las peticiones a `/meetings/1/summary`. Sin embargo, el endpoint `get_meeting_summary` es el que responde (verificado mediante monkey-patching y logs de debug — "DEBUG CALLED" nunca apareció en la función `get_meeting_summary_by_id`).

### Hipótesis

FastAPI (Starlette) parece estar ruteando `GET /meetings/1/summary` a la ruta 11 (`/{platform}/{native_meeting_id}/summary`) interpretando:
- `platform = "1"`
- `native_meeting_id = "summary"`

Esto sucede incluso cuando la ruta 10 con `{meeting_id:int}` está registrada primero.

### Evidencia

1. **TestClient vs server real**: El TestClient de Starlette también produce el mismo comportamiento (404), confirmando que no es un problema del server de producción.
2. **Orden de rutas**: Las rutas están en el orden correcto según `app.routes`.
3. **Route name en requests**: La función `get_meeting_summary_by_id` nunca es llamada (verificado con monkey-patching).
4. **Duplicate route 13**: Existe una ruta duplicada `/{platform}/{native_meeting_id}` (routes 8 y 13) — una para GET y otra para DELETE.

## Workaround Actual

Se implementó una solución defensiva en `get_meeting_summary` que detecta cuando `platform` es un número y redirige internamente:

```python
@router.get("/{platform}/{native_meeting_id}/summary", response_model=MeetingSummaryResponse)
async def get_meeting_summary(
    platform: str,
    native_meeting_id: str,
    db: Session = Depends(get_db),
):
    # Starlette routing bug: /meetings/1/summary → platform="1", native="summary"
    if platform.isdigit():
        return await get_meeting_summary_by_id(int(platform), db)
    # ... resto del código
```

También se cambió `{meeting_id:int}` a `{meeting_id}` (string) con conversión `int()` interna para evitar el mismo problema de routing.

## Solución Pendiente

La causa raíz — por qué Starlette rutea incorrectamente trotz having la ruta correcta primero — no está completamente entendida. Posibles direcciones de investigación:

1. **Orden de includes**: El orden en que se registran los routers en `main.py` podría afectar la prioridad de routing.
2. **APIRouter prefix handling**: Los prefijos de router podrían interactuar con el matching de rutas de forma no intuitiva.
3. **FastAPI/Starlette version**: Podría ser un bug en la versión específica usada.
4. **Ruta fantasma**: La ruta duplicada `/{platform}/{native_meeting_id}` (routes 8 y 13) podría estar interfiriendo.

## Verificación

```bash
# должно вернуть 200 с summary=null
curl http://localhost:8080/meetings/1/summary

# должно работать параллельно
curl http://localhost:8080/meetings/google_meet/rph-iyjx-vrt/summary
```

## Archivos Relacionados

- `app/routers/meetings.py` — endpoints de meetings y workaround de routing
- `app/routers/ui.py` — polling de la web UI usa `GET /meetings/{id}/summary`
