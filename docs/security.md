# Seguridad y Autenticación

Meety utiliza un sistema de autenticación basado en una **API Key estática** para proteger la instancia cuando se despliega en internet.

## Cómo Funciona

### Lado del Servidor
*   Variable: `MEETY_API_KEY` (Configurada en el entorno).
*   Validación: Todos los endpoints bajo `/meetings/*` requieren la cabecera `X-Meety-API-Key`.
*   SSE: El canal de tiempo real acepta la llave mediante el parámetro de consulta `?key=...`.

### Lado del Cliente (Web UI)
1.  Al detectar un error 401, el navegador muestra automáticamente un **Panel de Acceso**.
2.  La llave introducida se guarda en `localStorage`.
3.  Todas las peticiones futuras se firman automáticamente con esta llave.

## Configuración en Producción

Si despliegas en Coolify, debes definir la variable `MEETY_API_KEY`. Si se deja vacía, el sistema operará en "Modo Local" sin pedir contraseña.
