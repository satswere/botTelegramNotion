# Configuración de Tipster como Relación en Notion

## 📋 Descripción

El campo "Tipster" puede configurarse como una **Relación** (Relation) a otra base de datos de Tipsters en Notion. Esto permite:
- Mantener una lista centralizada de tipsters
- Rastrear estadísticas por tipster
- Crear dashboards y reportes avanzados

## 🔧 Configuración

### Paso 1: Crear Base de Datos de Tipsters

1. En Notion, crea una nueva base de datos llamada "Tipsters"
2. Asegúrate de que tenga una columna **Nombre** (tipo: Title)
3. Copia el **ID de la base de datos** (está en la URL)

### Paso 2: Configurar la Relación en tu Base de Apuestas

1. En tu base de datos de apuestas, agrega una columna llamada **Tipster**
2. Selecciona tipo: **Relation** (Relación)
3. Vincula a la base de datos de "Tipsters" que creaste

### Paso 3: Agregar la Variable de Entorno

Agrega esta línea a tu archivo `.env`:

```env
TIPSTER_DATABASE_ID=tu_id_de_base_de_datos_tipsters_aqui
```

## 🎯 Cómo Funciona

### Comportamiento Automático

El bot ahora:

1. **Si NO es un reenvío** → Busca/crea un tipster llamado "Personal"
2. **Si ES un reenvío** → Busca/crea un tipster con el nombre del remitente

### Proceso de Vinculación

```python
# El bot automáticamente:
1. Busca si el tipster ya existe en la base de Tipsters
2. Si existe → Lo vincula a la apuesta
3. Si NO existe → Lo crea automáticamente y luego lo vincula
```

## 📊 Estructura de la Base de Tipsters

Columnas recomendadas para tu base de datos de Tipsters:

| Columna | Tipo | Descripción |
|---------|------|-------------|
| **Nombre** | Title | Nombre del tipster (Personal, o nombre del canal) |
| Apuestas | Relation | Vinculado a tu base de apuestas (automático) |
| Total Apuestas | Rollup | Cuenta de apuestas relacionadas |
| Ganadas | Rollup | Filtro: Resultado = Ganada |
| Perdidas | Rollup | Filtro: Resultado = Perdida |
| ROI | Formula | Cálculo de retorno de inversión |

## ⚙️ Configuración Alternativa (Sin Base de Tipsters)

Si **NO** quieres usar una base de datos separada:

1. **NO** agregues `TIPSTER_DATABASE_ID` en `.env`
2. El bot automáticamente agregará la información del tipster en el campo "Mercado" como texto:

```
Mercado: Over 2.5 goles

📊 Deporte: Fútbol
🏆 Liga: No identificado
👤 Tipster: Personal
```

## 🧪 Ejemplo de Uso

### Con Base de Tipsters Configurada

```python
# En .env
TIPSTER_DATABASE_ID=abc123def456

# Resultado:
# - Campo "Tipster" → Relación a página de tipster
# - Campo "Mercado" → Solo información de mercado
```

### Sin Base de Tipsters

```python
# En .env
# (no incluir TIPSTER_DATABASE_ID)

# Resultado:
# - Campo "Tipster" → NO se crea
# - Campo "Mercado" → Incluye info de tipster como texto
```

## 🔍 Verificación

Para verificar que funciona correctamente:

1. Envía una imagen de apuesta al bot
2. Ve a tu base de datos de apuestas
3. Verifica que:
   - El campo "Tipster" tenga una relación (si configuraste la base de Tipsters)
   - O el campo "Mercado" incluya la info del tipster (si no configuraste la base)

## 🐛 Solución de Problemas

### Error: "Tipster is expected to be relation"

**Causa**: La columna "Tipster" existe en tu base de datos pero NO está configurada como relación.

**Solución**:
1. Elimina la columna "Tipster" de tu base de datos de apuestas, O
2. Cambia su tipo a "Relation" y vincúlala a una base de Tipsters, O
3. Elimina `TIPSTER_DATABASE_ID` del `.env` para usar la alternativa de texto

### Error: "Cannot find property Nombre in Tipster database"

**Causa**: Tu base de Tipsters no tiene una columna "Nombre" de tipo Title.

**Solución**: Asegúrate de que la base de Tipsters tenga una columna principal llamada "Nombre" (tipo: Title).

## 📝 Notas

- El sistema crea automáticamente nuevos tipsters cuando detecta nombres que no existen
- "Personal" se usa para apuestas que NO son reenvíos
- Para reenvíos, se usa el nombre del canal/usuario que envió el mensaje original
