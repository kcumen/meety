# Arquitectura del Sistema

Meety es una aplicación modular construida con FastAPI, diseñada para la eficiencia y la escalabilidad personal.

## Componentes Principales

1.  **FastAPI Core**: Gestión de rutas y lógica de negocio.
2.  **SQLAlchemy (SQLite)**: Persistencia ligera de reuniones y transcripciones.
3.  **Vexa Client**: Integración con la API de bots de Vexa.ai.
4.  **AI Engine (OpenRouter)**: Procesamiento de transcripciones para generar resúmenes ejecutivos y listas de tareas.
5.  **Notifier Service**: Motor de suscripción SSE para el frontend.

## Flujo de Datos

1.  **Solicitud**: El usuario pega una URL → El backend pide un bot a Vexa.
2.  **Webhook**: Vexa notifica cambios → El backend actualiza la DB y avisa por SSE.
3.  **Finalización**: Vexa avisa del fin → El backend descarga transcripción → Llama a la IA → Notifica por Telegram y SSE.
4.  **Consulta**: El usuario abre la web → Ve el resumen formateado al instante.
