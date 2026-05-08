# Meety 🤖

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Meety** es un asistente de reuniones inteligente que automatiza la captura, transcripción y resumen de tus videollamadas en Google Meet, Microsoft Teams y Zoom. Diseñado para la eficiencia, Meety te permite concentrarte en la conversación mientras él se encarga de la documentación.

---

## ✨ Características Principales

- 🤖 **Integración Universal**: Soporte para las principales plataformas de videollamada vía [vexa.ai](https://vexa.ai).
- 📝 **Transcripción en Tiempo Real**: Captura cada palabra con precisión quirúrgica.
- 🧠 **Resúmenes Inteligentes**: Generación automática de minutas, puntos clave y tareas pendientes usando LLMs (vía OpenRouter).
- ⚡ **Interfaz Premium**: Dashboard minimalista con actualizaciones en tiempo real (SSE).
- 🔒 **Seguridad por Dispositivo**: Acceso protegido mediante API Keys cifradas en el navegador.
- 🐳 **Docker & Podman Ready**: Despliegue sencillo y consistente en cualquier entorno.
- 💬 **Notificaciones**: Integración opcional con Telegram para recibir tus resúmenes al instante.

---

## 🚀 Inicio Rápido

### 1. Requisitos Previos
- Python 3.11+ o Podman/Docker.
- API Keys de: [Vexa.ai](https://vexa.ai) y [OpenRouter](https://openrouter.ai).

### 2. Instalación Local
```bash
# Clonar repositorio
git clone https://github.com/kcumen/meety.git && cd meety

# Configurar entorno
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# [Edita el archivo .env con tus llaves]

# Iniciar servidor
uvicorn app.main:app --reload --port 8080
```

### 3. Ejecución con Contenedores (Podman/Docker)
```bash
podman compose up --build -d
```
*Accede a la interfaz en: `http://localhost:8080`*

---

## 🛠️ Stack Tecnológico

- **Backend**: FastAPI (Python)
- **Base de Datos**: SQLite + SQLAlchemy (Async)
- **Real-time**: Server-Sent Events (SSE)
- **AI**: Vexa.ai (Bot) + OpenRouter (Modelos Claude/GPT)
- **Deployment**: Docker / Coolify

---

## 📚 Documentación del Proyecto

Explora los detalles técnicos y guías de configuración:

- 🌐 [**Webhooks & Integración**](docs/webhooks.md): Cómo conectar Meety con servicios externos.
- 🔄 [**Sistema Real-time**](docs/realtime.md): Detalles sobre la arquitectura SSE y notificaciones.
- 🛡️ [**Seguridad & Auth**](docs/security.md): Explicación del sistema de protección y cifrado.
- 🚢 [**Guía de Despliegue**](docs/deployment.md): Instrucciones para Coolify y entornos Docker.
- 🏗️ [**Arquitectura**](docs/architecture.md): Vista técnica general del sistema.
- 🚀 [**Roadmap Interactivo**](docs/interactive_bots.md): Futuras capacidades de voz y chat del bot.

---

## 🤝 Contribuir

Si quieres mejorar Meety, ¡siéntete libre de abrir un Pull Request o reportar un Issue!

---
Developed with ❤️ by **Kcumen Team**
