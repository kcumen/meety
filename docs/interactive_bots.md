# Capacidades Interactivas (Hoja de Ruta)

Este documento detalla las capacidades de **Interactive Bots** de Vexa.ai y cómo podrían integrarse en Meety en el futuro para convertir al bot en un participante activo.

## 1. Visión General
Los "Bots Interactivos" permiten controlar la voz, el chat y el contenido visual (pantalla compartida) del bot durante una reunión activa mediante comandos REST.

**Requisito técnico:** El bot debe ser creado con `voice_agent_enabled: true` (configurado por defecto en Meety).

## 2. Capacidades de Control

### 🎙️ Voz (Text-to-Speech)
El bot puede hablar en la reunión, desmuteándose automáticamente y volviéndose a mutear al finalizar.
- **Uso potencial**: Presentación de resúmenes finales, saludos de bienvenida o traducción simultánea por audio.
- **Proveedores**: Soporta OpenAI (voces como `alloy`, `nova`, `shimmer`) y audio pre-renderizado (URL o Base64).

### 💬 Chat (Lectura y Escritura)
El bot puede interactuar con el chat nativo de la plataforma (Meet, Teams, Zoom).
- **Escritura**: Enviar minutas, enlaces o respuestas a comandos.
- **Lectura**: Capturar mensajes de otros participantes para ejecutar acciones (ej: responder a "!resumen").

### 🖥️ Pantalla Compartida (Visuales)
El bot puede compartir su "escritorio virtual" para mostrar contenido a los participantes.
- **Tipos de contenido**: Imágenes, URLs (dashboards, slides), Videos (MP4) o HTML personalizado.
- **Uso potencial**: Proyectar la transcripción en vivo, mostrar gráficas de datos mencionados o presentaciones corporativas.

### 👤 Avatar y Cámara
- **Avatar**: Cambiar la imagen del bot en su recuadro de video.
- **Uso potencial**: Mostrar estados visuales (ej: "Procesando...", "Escuchando...") o branding dinámico.

## 3. Casos de Uso Futuros para Meety

1.  **Bot Moderador**: Responder a preguntas en el chat sobre lo que se ha dicho anteriormente en la reunión usando RAG (Retrieval-Augmented Generation).
2.  **Presentador de Minutas**: Al detectar que la reunión está terminando, el bot pide la palabra y resume los acuerdos en voz alta.
3.  **Traductor Universal**: Escuchar en un idioma y proyectar/decir la traducción para los demás participantes.
4.  **Visualizador de Contexto**: Compartir pantalla con una página HTML que muestre conceptos clave, nombres mencionados y tareas pendientes en tiempo real.

## 4. Referencia de API (Vexa)
Endpoints principales:
- `POST /bots/.../speak`: Enviar texto para hablar.
- `POST /bots/.../chat`: Enviar mensaje al chat.
- `POST /bots/.../screen`: Empezar a compartir contenido visual.
- `DELETE /bots/.../speak`: Interrumpir el habla actual.

---
*Documento generado para futura implementación de la Fase 2 de Meety.*
