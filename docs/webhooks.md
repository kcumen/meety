# Integración de Webhooks (Vexa.ai)

Meety utiliza webhooks para reaccionar en tiempo real a los cambios en las reuniones gestionadas por Vexa.ai.

## Configuración

El webhook debe apuntar a: `{APP_BASE_URL}/webhook/vexa`

## Eventos Soportados

El sistema está preparado para procesar los siguientes eventos de Vexa:

1.  **`meeting.started`**: Actualiza el estado de la reunión a `active` en la base de datos y notifica a la UI.
2.  **`meeting.completed`**: 
    *   Cambia el estado a `completed`.
    *   Dispara la descarga de la transcripción.
    *   Genera el resumen automático con IA.
    *   Envía notificaciones (Telegram).
3.  **`bot.failed`**: Marca la reunión como `failed` y notifica el error a la interfaz.
4.  **`meeting.status_change`**: Mapeo dinámico de estados intermedios (ej: `joining`, `awaiting_admission`).

## Procesamiento Asíncrono

Para garantizar una respuesta rápida (200 OK) a Vexa, todo el procesamiento pesado (IA, base de datos, descargas) se realiza mediante **Background Tasks** de FastAPI.

## Estructura de Datos

El sistema soporta tanto la estructura plana como la anidada (`data.meeting`) que utiliza Vexa en diferentes versiones de su API.
