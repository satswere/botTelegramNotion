#!/bin/bash
# ===========================================================================
# Deploy Telegram-Notion Bot to Azure Container Apps
# ===========================================================================
# Prerequisites:
#   - Azure CLI installed (az)
#   - Docker installed
#   - Logged in to Azure: az login
# ===========================================================================

set -e

# ==================== CONFIGURATION ====================
# Modify these variables according to your needs
RESOURCE_GROUP="rg-telegram-notion-bot"
LOCATION="eastus"
ACR_NAME="acrtelegramnotionbot"  # Must be globally unique, lowercase, no hyphens
CONTAINER_APP_ENV="cae-telegram-bot"
CONTAINER_APP_NAME="ca-telegram-bot"
IMAGE_NAME="telegram-notion-bot"
IMAGE_TAG="latest"

# ==================== STEP 1: Create Resource Group ====================
echo "Creating resource group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# ==================== STEP 2: Create Azure Container Registry ====================
echo "Creating Azure Container Registry..."
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

# ==================== STEP 3: Build and Push Image ====================
echo "Building and pushing Docker image..."
az acr build \
  --registry $ACR_NAME \
  --image $IMAGE_NAME:$IMAGE_TAG \
  .

# ==================== STEP 4: Create Container Apps Environment ====================
echo "Creating Container Apps Environment..."
az containerapp env create \
  --name $CONTAINER_APP_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# ==================== STEP 5: Get ACR Credentials ====================
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

# ==================== STEP 6: Deploy Container App ====================
echo "Deploying Container App..."
az containerapp create \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_APP_ENV \
  --image "$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG" \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_NAME \
  --registry-password "$ACR_PASSWORD" \
  --cpu 0.25 \
  --memory 0.5Gi \
  --min-replicas 1 \
  --max-replicas 1 \
  --secrets \
    telegram-token="<YOUR_TELEGRAM_BOT_TOKEN>" \
    notion-token="<YOUR_NOTION_TOKEN>" \
    notion-db-id="<YOUR_NOTION_DATABASE_ID>" \
    openai-key="<YOUR_OPENAI_API_KEY>" \
    openai-url="<YOUR_OPENAI_API_URL>" \
  --env-vars \
    TELEGRAM_BOT_TOKEN=secretref:telegram-token \
    NOTION_TOKEN=secretref:notion-token \
    NOTION_DATABASE_ID=secretref:notion-db-id \
    OPENAI_API_KEY=secretref:openai-key \
    OPENAI_API_URL=secretref:openai-url

echo ""
echo "✅ Deployment complete!"
echo "Container App: $CONTAINER_APP_NAME"
echo ""
echo "To view logs:"
echo "  az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --follow"
echo ""
echo "To update after code changes:"
echo "  az acr build --registry $ACR_NAME --image $IMAGE_NAME:$IMAGE_TAG ."
echo "  az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --image $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG"
