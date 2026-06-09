# ===========================================================================
# Deploy Telegram-Notion Bot to Azure Container Apps (PowerShell)
# ===========================================================================
# Prerequisites:
#   - Azure CLI installed (az)
#   - Docker installed
#   - Logged in to Azure: az login
# ===========================================================================

$ErrorActionPreference = "Stop"

# ==================== CONFIGURATION ====================
$RESOURCE_GROUP = "rg-telegram-notion-bot"
$LOCATION = "eastus"
$ACR_NAME = "acrtelegramnotionbot"  # Must be globally unique, lowercase, no hyphens
$CONTAINER_APP_ENV = "cae-telegram-bot"
$CONTAINER_APP_NAME = "ca-telegram-bot"
$IMAGE_NAME = "telegram-notion-bot"
$IMAGE_TAG = "latest"

# ==================== STEP 1: Create Resource Group ====================
Write-Host "Creating resource group..." -ForegroundColor Cyan
az group create --name $RESOURCE_GROUP --location $LOCATION

# ==================== STEP 2: Create Azure Container Registry ====================
Write-Host "Creating Azure Container Registry..." -ForegroundColor Cyan
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# ==================== STEP 3: Build and Push Image ====================
Write-Host "Building and pushing Docker image..." -ForegroundColor Cyan
az acr build --registry $ACR_NAME --image "${IMAGE_NAME}:${IMAGE_TAG}" .

# ==================== STEP 4: Create Container Apps Environment ====================
Write-Host "Creating Container Apps Environment..." -ForegroundColor Cyan
az containerapp env create --name $CONTAINER_APP_ENV --resource-group $RESOURCE_GROUP --location $LOCATION

# ==================== STEP 5: Get ACR Credentials ====================
$ACR_LOGIN_SERVER = az acr show --name $ACR_NAME --query loginServer -o tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv

# ==================== STEP 6: Deploy Container App ====================
Write-Host "Deploying Container App..." -ForegroundColor Cyan

# IMPORTANT: Replace these placeholders with your actual secrets
$TELEGRAM_TOKEN = "<YOUR_TELEGRAM_BOT_TOKEN>"
$NOTION_TOKEN = "<YOUR_NOTION_TOKEN>"
$NOTION_DB_ID = "<YOUR_NOTION_DATABASE_ID>"
$OPENAI_KEY = "<YOUR_OPENAI_API_KEY>"
$OPENAI_URL = "<YOUR_OPENAI_API_URL>"

az containerapp create `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --environment $CONTAINER_APP_ENV `
  --image "$ACR_LOGIN_SERVER/${IMAGE_NAME}:${IMAGE_TAG}" `
  --registry-server $ACR_LOGIN_SERVER `
  --registry-username $ACR_NAME `
  --registry-password $ACR_PASSWORD `
  --cpu 0.25 `
  --memory 0.5Gi `
  --min-replicas 1 `
  --max-replicas 1 `
  --secrets "telegram-token=$TELEGRAM_TOKEN" "notion-token=$NOTION_TOKEN" "notion-db-id=$NOTION_DB_ID" "openai-key=$OPENAI_KEY" "openai-url=$OPENAI_URL" `
  --env-vars "TELEGRAM_BOT_TOKEN=secretref:telegram-token" "NOTION_TOKEN=secretref:notion-token" "NOTION_DATABASE_ID=secretref:notion-db-id" "OPENAI_API_KEY=secretref:openai-key" "OPENAI_API_URL=secretref:openai-url"

Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Container App: $CONTAINER_APP_NAME"
Write-Host ""
Write-Host "To view logs:"
Write-Host "  az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --follow"
Write-Host ""
Write-Host "To update after code changes:"
Write-Host "  az acr build --registry $ACR_NAME --image ${IMAGE_NAME}:${IMAGE_TAG} ."
Write-Host "  az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --image $ACR_LOGIN_SERVER/${IMAGE_NAME}:${IMAGE_TAG}"
