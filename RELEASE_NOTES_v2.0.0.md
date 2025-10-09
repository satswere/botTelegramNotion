# v2.0.0 – Subida Real a Notion | Reenvíos Inteligentes | Análisis con OpenAI

## 🧩 Resumen
Esta versión mayor consolida el bot en un único script (`bot_main.py`), añade la subida REAL de archivos a Notion mediante su flujo oficial, integra análisis automático de tickets con OpenAI (visión) y detecta/estructura información de mensajes reenviados (usuarios, canales, privados, hash único). Reduce ruido legacy y sienta base para futuras extensiones (estadísticas, API, CI/CD).

---

## ✨ Novedades Principales (Highlights)
- Subida real a Notion (3 pasos: `file_uploads` → upload multipart → `pages.create`)
- Análisis de imágenes (tickets Bet365) con OpenAI Vision → JSON estructurado
- Detección avanzada de reenvíos (API moderna + legacy, hash único de origen)
- Registro unificado con propiedades Notion correctas y archivo adjunto real
- Limpieza masiva de archivos duplicados y simplificación de estructura
- Logging consistente (archivo + consola) con trazabilidad extendida

---

## 🆕 Funcionalidades Detalladas
| Área | Detalle |
|------|---------|
| Notion | Uso de `file_upload` (no enlaces externos) |
| OpenAI | Prompt especializado para extraer: Evento, Mercado, Selección, Cuota, Monto, Ganancia Potencial, Estado |
| Reenvíos | Compatibilidad con `forward_origin`, campos legacy y usuarios privados (hash MD5 parcial) |
| Comandos | `/start`, `/help`, `/status` |
| Parsing | Limpieza de bloques ```json y validación segura |
| Nombres Notion | Alineados: Evento / Selección, Captura / Comprobante, Mercado, Seleccion, Cuota, Importe apostado |

---

## 🛠 Cambios Técnicos
- Validación temprana de variables críticas (.env)
- Timestamp granular en nombres de archivos (`photo_YYYYmmdd_HHMMSS_mmm.ext`)
- Manejo tolerante de números (cuota, importe)
- Estructura de mensajes enriquecida (forward + sender + chat + origin)
- Refactor a un “bot monolítico claro” orientado a extensibilidad
- Aislamiento de análisis en `OpenAIHandler`

---

## ⚠ Breaking Changes
| Cambio | Impacto | Mitigación |
|--------|---------|-----------|
| Eliminados scripts `bot_*` antiguos | Rutas o automatizaciones previas fallarán | Usar solo `bot_main.py` |
| Nuevas variables OpenAI | Fallo en inicialización si faltan | Añadir al `.env` (ver tabla) |
| Propiedades Notion esperadas | Si faltan, error al crear página | Crear/renombrar propiedades en la base |

---

## 🧪 Estado de Calidad
| Aspecto | Estado |
|---------|--------|
| Descarga imágenes | OK |
| Subida Notion (archivo real) | OK |
| Análisis OpenAI visión | OK (con fallback si falla) |
| Manejo reenvíos | OK (usuario → canal → privado) |
| Comando `/status` | OK |
| Logs | OK (archivo + consola) |
| Tests legacy | Limitados (pendiente ampliar) |

---

## 🔐 Variables de Entorno Requeridas
| Variable | Descripción | Obligatoria | Ejemplo |
|----------|-------------|------------|---------|
| TELEGRAM_BOT_TOKEN | Token del Bot de Telegram | Sí | 123456:ABC... |
| NOTION_TOKEN | Token de integración interna | Sí | secret_abc123 |
| NOTION_DATABASE_ID | ID de la base de datos Notion | Sí | 27aa8b...0fa0 |
| OPENAI_API_KEY | Clave acceso API visión | Sí | sk-... |
| OPENAI_API_URL | Endpoint base (Azure/OpenAI proxy) | Sí | https://.../deployments/vision |
| API_VERSION | Versión API usada | Sí | 2024-02-15 |
| LOG_LEVEL (opcional) | Nivel de logs | No | INFO |

---

## 📋 Propiedades esperadas en tu Base de Notion
| Nombre (Exacto) | Tipo |
|-----------------|------|
| Evento / Selección | Title |
| Fecha | Date |
| Resultado | Select |
| Casa de apuestas | Select |
| Tipo de apuesta | Select |
| Captura / Comprobante | Files |
| Mercado | Rich Text |
| Seleccion | Rich Text |
| Cuota | Number |
| Importe apostado | Number |

---

## 🚀 Instalación (Fresh Setup)
```bash
pip install -r requirements.txt
python bot_main.py
```
Enviar una imagen al bot → debería:
1. Responder con “Procesando…”
2. Subir archivo real a Notion
3. Mostrar análisis JSON en el chat
4. Adjuntar info de reenvío (si aplica)

---

## 🔄 Upgrade desde v1.x
1. Elimina scripts antiguos (si tenías automatizaciones)
2. Actualiza dependencias:
```bash
pip install -r requirements.txt --upgrade
```
3. Ajusta `.env` con nuevas claves OpenAI
4. Verifica propiedades de la base
5. Ejecuta `/status` para probar conexión
6. Envía un mensaje reenviado y confirma que aparece el bloque de origen

---

## 🧪 Checklist Post-Deploy
- [ ] `/status` devuelve “Notion ✅”
- [ ] Imagen → aparece en Notion como archivo (no URL externa)
- [ ] Análisis JSON contiene campos (aunque algunos sean “No especificado”)
- [ ] Reenvío desde canal → se ve ID origen
- [ ] Reenvío desde usuario privado → se ve etiqueta privado + hash
- [ ] Campo “Cuota” se guarda como número válido

---

## 🐞 Known Issues / Limitaciones
| Ítem | Descripción | Prioridad |
|------|-------------|-----------|
| Importe apostado fijo (500) | Falta parseo robusto y mapeo dinámico | Media |
| Sin reintentos en fallos OpenAI | Un fallo aborta análisis | Media |
| Sin tests automatizados del flujo Notion | Riesgo regresión | Alta |
| No se mapean todos los campos extraídos (Ganancia, Estado) | JSON visible pero no persistido completo | Media |

---

## 🗺 Roadmap Sugerido
- Mapear Ganancia Potencial y Estado a propiedades Notion
- Añadir retry con `tenacity` en upload y análisis
- Tests (pytest + fixtures simulando Notion / Telegram)
- Docker + pipeline CI/CD
- Comando `/stats` y exportaciones

---

## 📦 Dependencias Clave
```
python-telegram-bot >= 22.0
notion-client >= 2.2.1
aiohttp >= 3.8.0
Pillow >= 10.0.0
openai >= 1.3.0
```

---

## 🧾 CHANGELOG (formato “Keep a Changelog”)
### [2.0.0] - 2025-09-30
#### Added
- Subida real de archivos a Notion (file_uploads)
- Análisis de tickets con OpenAI visión + prompt especializado
- Detección de origen de reenvío (usuario/canal/privado)
- Comando `/status` con verificación de base de datos
- Limpieza JSON de análisis y validación segura
#### Changed
- Consolidación en único script `bot_main.py`
- Refactor logging y estructura de respuesta al usuario
#### Fixed
- Nombres de extensiones preservados al descargar imágenes
- Manejo seguro de campos numéricos (cuota / monto)
#### Removed
- Scripts legacy (`bot_*` anteriores)
- Documentación redundante no esencial
#### Security
- Validación temprana de variables de entorno obligatorias

---

## 🪪 Identificador Interno
Ref: Reestructuración 26–30 Sep 2025 / Base estable para v2.x

---

## 🧴 Versión Corta (para copia rápida)
v2.0.0 – Subida real a Notion, análisis AI de tickets (OpenAI), detección inteligente de reenvíos y consolidación del bot. Nuevas variables de entorno (OPENAI_*). Ajusta propiedades en Notion antes de actualizar.
