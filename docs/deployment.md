# Guía de Despliegue (Docker & Coolify)

Meety está diseñado para ser desplegado de forma sencilla y persistente mediante contenedores. Esta guía se enfoca en el despliegue profesional usando **Coolify**.

## 🚀 Configuración en Coolify

### 1. Creación del Servicio
- Conecta tu repositorio de GitHub a un nuevo recurso en Coolify.
- Selecciona el modo **Dockerfile**. Coolify leerá automáticamente el archivo en la raíz.

### 2. Variables de Entorno
Configura las siguientes variables en la pestaña **Environment Variables**:
- `APP_BASE_URL`: URL pública final (ej: `https://meety.tudominio.com`). **Crucial** para los webhooks.
- `VEXA_API_KEY`: Tu API Key de Vexa.ai.
- `OPENROUTER_API_KEY`: Tu API Key de OpenRouter.
- `MEETY_API_KEY`: La clave que usarás para entrar a la interfaz (se guardará cifrada en tu navegador).

### 3. Persistencia de Datos (Crítico) 💾
Para no perder las reuniones y transcripciones al actualizar la imagen, debes configurar un volumen:
1. Ve a **Storage** > **Add Directory Mount**.
2. **Source Directory**: `meety_data` (o una ruta en el servidor como `/data/meety`).
3. **Destination Directory**: `/app/data`
4. Haz clic en **Add**.

### 4. Automatización del Webhook 🔄
Para que Vexa sepa dónde enviar las actualizaciones sin que tengas que configurarlo manualmente:
1. Ve a la pestaña **Post-deployment Command** (o similar en la configuración del build).
2. Añade el siguiente comando:
   ```bash
   python scratch/set_webhook.py
   ```
   *Este script usará automáticamente tu `APP_BASE_URL` para registrar el webhook en Vexa.ai.*

## 🛠️ Mantenimiento y Logs

### Ver Logs del Contenedor
Si necesitas depurar algo, usa el panel de logs de Coolify o mediante consola:
```bash
podman logs -f meety
```

### Health Check
Meety expone un endpoint de salud en `/health` que devuelve `{"status":"ok"}`. Puedes configurarlo en la sección de Health Check de Coolify para asegurar que el contenedor está respondiendo correctamente.

---
*Documentación actualizada tras pruebas exitosas de despliegue.*
