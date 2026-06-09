# Despliegue en Azure

## Opción recomendada: Azure Container Apps

Tu bot usa **polling** (no webhooks), así que necesita un proceso que corra 24/7. Azure Container Apps es ideal porque:
- Precio bajo (~$5-10/mes con 0.25 vCPU + 0.5GB RAM)
- No necesita configurar networking complejo
- Soporte nativo para secretos
- Logs integrados

## Requisitos previos

1. [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli) instalado
2. Una suscripción de Azure activa
3. Sesión iniciada: `az login`

## Pasos de despliegue

### Opción A: Script automático (recomendado)

**PowerShell (Windows):**
```powershell
# 1. Edita deploy-azure.ps1 y reemplaza los placeholders de secretos
# 2. Ejecuta:
.\deploy-azure.ps1
```

**Bash (Linux/Mac/WSL):**
```bash
chmod +x deploy-azure.sh
# 1. Edita deploy-azure.sh y reemplaza los placeholders de secretos
# 2. Ejecuta:
./deploy-azure.sh
```

### Opción B: Paso a paso manual

```bash
# 1. Crear Resource Group
az group create --name rg-telegram-notion-bot --location eastus

# 2. Crear Container Registry
az acr create --resource-group rg-telegram-notion-bot --name acrtelegramnotionbot --sku Basic --admin-enabled true

# 3. Construir imagen en la nube (no necesitas Docker local)
az acr build --registry acrtelegramnotionbot --image telegram-notion-bot:latest .

# 4. Crear Container Apps Environment
az containerapp env create --name cae-telegram-bot --resource-group rg-telegram-notion-bot --location eastus

# 5. Desplegar (reemplaza <valores>)
az containerapp create \
  --name ca-telegram-bot \
  --resource-group rg-telegram-notion-bot \
  --environment cae-telegram-bot \
  --image acrtelegramnotionbot.azurecr.io/telegram-notion-bot:latest \
  --registry-server acrtelegramnotionbot.azurecr.io \
  --registry-username acrtelegramnotionbot \
  --registry-password "$(az acr credential show --name acrtelegramnotionbot --query 'passwords[0].value' -o tsv)" \
  --cpu 0.25 --memory 0.5Gi \
  --min-replicas 1 --max-replicas 1 \
  --secrets \
    telegram-token="<TU_TELEGRAM_BOT_TOKEN>" \
    notion-token="<TU_NOTION_TOKEN>" \
    notion-db-id="<TU_NOTION_DATABASE_ID>" \
    openai-key="<TU_OPENAI_API_KEY>" \
    openai-url="<TU_OPENAI_API_URL>" \
  --env-vars \
    TELEGRAM_BOT_TOKEN=secretref:telegram-token \
    NOTION_TOKEN=secretref:notion-token \
    NOTION_DATABASE_ID=secretref:notion-db-id \
    OPENAI_API_KEY=secretref:openai-key \
    OPENAI_API_URL=secretref:openai-url
```

## Variables de entorno necesarias

| Variable | Descripción |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram |
| `NOTION_TOKEN` | Token de integración de Notion |
| `NOTION_DATABASE_ID` | ID de la base de datos de Notion |
| `OPENAI_API_KEY` | API key de OpenAI |
| `OPENAI_API_URL` | URL del endpoint de OpenAI |
| `TIPSTER_DATABASE_ID` | (Opcional) ID de la DB de Tipsters |

## Operaciones comunes

### Ver logs en tiempo real
```bash
az containerapp logs show --name ca-telegram-bot --resource-group rg-telegram-notion-bot --follow
```

### Actualizar después de cambios en el código
```bash
az acr build --registry acrtelegramnotionbot --image telegram-notion-bot:latest .
az containerapp update --name ca-telegram-bot --resource-group rg-telegram-notion-bot --image acrtelegramnotionbot.azurecr.io/telegram-notion-bot:latest
```

### Reiniciar el bot
```bash
az containerapp revision restart --name ca-telegram-bot --resource-group rg-telegram-notion-bot
```

### Detener el bot (para no gastar)
```bash
az containerapp update --name ca-telegram-bot --resource-group rg-telegram-notion-bot --min-replicas 0 --max-replicas 0
```

### Reanudar el bot
```bash
az containerapp update --name ca-telegram-bot --resource-group rg-telegram-notion-bot --min-replicas 1 --max-replicas 1
```

## Costos estimados

| Recurso | Costo aprox/mes |
|---------|-----------------|
| Container Apps (0.25 vCPU, 0.5GB, 24/7) | ~$7 |
| Container Registry (Basic) | ~$5 |
| **Total** | **~$12/mes** |

## Nota sobre almacenamiento de imágenes

El bot guarda imágenes localmente en `storage/images/`. En Azure Container Apps el almacenamiento es efímero (se pierde al reiniciar). Las imágenes ya se suben a Notion via `NotionFileUploader`, así que no debería ser problema. Si necesitas persistencia, puedes montar un Azure File Share.
