#!/usr/bin/env bash
set -euo pipefail

# === CONFIG ===
REGION="us-west-1"
ACCOUNT_ID="049306851249"
REPO_NAME="rag-app"
IMAGE_TAG="latest"
FUNCTION_NAME_PROXY="rag-proxy"
FUNCTION_NAME_SERVER="rag-server"
FUNCTION_NAME_BACKGROUND="rag-background"
DOCKERFILE="./docker/Dockerfile.lambda"
BUILD_ARG_CACHE_BREAK=$(date +%s)

# === Help message ===
usage() {
  echo "Usage: $0 [--region R] [--account A] [--repo R] [--tag T] [--dockerfile F] [--functions \"fn1 fn2 ...\"]"
  echo
  echo "Defaults:"
  echo "  REGION=$REGION"
  echo "  ACCOUNT_ID=$ACCOUNT_ID"
  echo "  REPO_NAME=$REPO_NAME"
  echo "  IMAGE_TAG=$IMAGE_TAG"
  echo "  DOCKERFILE=$DOCKERFILE"
  echo "  FUNCTIONS=${FUNCTIONS[*]}"
  exit 1
}

# === Flag parsing ===
while [[ $# -gt 0 ]]; do
  case "$1" in
    --region) REGION="$2"; shift 2 ;;
    --account) ACCOUNT_ID="$2"; shift 2 ;;
    --repo) REPO_NAME="$2"; shift 2 ;;
    --tag) IMAGE_TAG="$2"; shift 2 ;;
    --dockerfile) DOCKERFILE="$2"; shift 2 ;;
    --functions) IFS=' ' read -r -a FUNCTIONS <<< "$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

# === Derived values ===
ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
ECR_REPO_URI="${ECR_REGISTRY}/${REPO_NAME}"
IMAGE_URI="${ECR_REPO_URI}:${IMAGE_TAG}"

# === Display summary ===
echo "========================================"
echo " 🚀 Lambda Deployment Summary"
echo "----------------------------------------"
echo " Region      : $REGION"
echo " Account ID  : $ACCOUNT_ID"
echo " Repo Name   : $REPO_NAME"
echo " Image Tag   : $IMAGE_TAG"
echo " Dockerfile  : $DOCKERFILE"
echo " Functions   : ${FUNCTIONS[*]}"
echo " Cache Break : $BUILD_ARG_CACHE_BREAK"
echo " Image URI   : $IMAGE_URI"
echo "========================================"

# === Step 1: Ensure ECR repository exists ===
if ! aws ecr describe-repositories --repository-names "$REPO_NAME" --region "$REGION" >/dev/null 2>&1; then
  echo "📦 Creating ECR repository: $REPO_NAME"
  aws ecr create-repository --repository-name "$REPO_NAME" --region "$REGION" >/dev/null
else
  echo "✅ ECR repository already exists."
fi

# === Step 2: Log in to ECR ===
echo "🔐 Logging in to AWS ECR..."
aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "$ECR_REGISTRY"

# === Step 3: Build Docker image ===
echo "🔨 Building Docker image from $DOCKERFILE..."
docker build --no-cache -t "${REPO_NAME}:${IMAGE_TAG}" -f "$DOCKERFILE" . \
  --build-arg CACHE_BREAK="$BUILD_ARG_CACHE_BREAK"

# === Step 4: Tag + Push image ===
echo "🏷️ Tagging image as $IMAGE_URI"
docker tag "${REPO_NAME}:${IMAGE_TAG}" "$IMAGE_URI"

echo "📤 Pushing image to ECR..."
docker push "$IMAGE_URI"

# === Step 5: Update all Lambda functions ===
for fn in "${FUNCTIONS[@]}"; do
  echo "🚀 Updating Lambda function: $fn"
  aws lambda update-function-code \
    --function-name "$fn" \
    --region "$REGION" \
    --image-uri "$IMAGE_URI" > /dev/null

  echo "⏳ Waiting for $fn deployment to finish..."

  # Wait until deployment status is Successful (or fail early)
  for i in {1..30}; do
    status=$(aws lambda get-function-configuration \
      --function-name "$fn" \
      --region "$REGION" \
      --query "LastUpdateStatus" \
      --output text)

    if [[ "$status" == "Successful" ]]; then
      echo "✅ $fn deployment complete."
      break
    elif [[ "$status" == "Failed" ]]; then
      echo "❌ Deployment failed for $fn"
      exit 1
    else
      sleep 1
    fi
  done

  # Timeout if status never becomes Successful
  if [[ "$status" != "Successful" ]]; then
    echo "⚠️ Timeout waiting for $fn to finish updating"
    exit 1
  fi
done


echo "🎉 Deployment complete!"