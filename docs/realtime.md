# Actualizaciones en Tiempo Real (SSE)

Meety implementa **Server-Sent Events (SSE)** para actualizar la interfaz de usuario instantáneamente sin necesidad de recargar la página.

## Arquitectura

1.  **Servicio Notifier**: Un bus de eventos en memoria (`app/services/notifier.py`) que gestiona las suscripciones de los clientes.
2.  **Endpoint**: `GET /meetings/events`
    *   Mantiene una conexión abierta con el navegador.
    *   Transmite eventos en formato JSON: `{"event": "tipo", "data": {...}}`.
3.  **Frontend**: Utiliza `EventSource` para escuchar los mensajes y disparar actualizaciones en el DOM.

## Ventajas sobre Polling

*   **Menos Carga**: El servidor no recibe peticiones constantes cada pocos segundos.
*   **Instantáneo**: El cambio de estado (ej: de "Esperando" a "Activa") se refleja en milisegundos tras recibir el webhook de Vexa.
*   **Eficiencia**: Utiliza una única conexión persistente HTTP.
