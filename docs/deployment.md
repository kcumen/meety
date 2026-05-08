# Despliegue con Docker y Coolify

Meety está optimizado para ser desplegado en contenedores mediante Docker.

## Archivos de Configuración

*   **`Dockerfile`**: Imagen optimizada basada en Python 3.11-slim. Utiliza `gunicorn` para estabilidad productiva.
*   **`docker-compose.yml`**: Define el servicio, las variables de entorno y el volumen de persistencia.

## Despliegue en Coolify

1.  Conecta tu repositorio de GitHub.
2.  Coolify detectará el `Dockerfile` automáticamente.
3.  **Variables de Entorno Críticas**:
    *   `APP_BASE_URL`: URL pública del despliegue (ej: `https://meety.tudominio.com`).
    *   `VEXA_API_KEY`: Tu llave de Vexa.ai.
    *   `OPENROUTER_API_KEY`: Para la generación de resúmenes.
    *   `MEETY_API_KEY`: Tu clave de acceso personal.

## Persistencia

La base de datos SQLite se almacena en `/app/data/meety.db`. Es vital configurar el volumen en Coolify para no perder los datos en cada actualización de imagen.
