#!/bin/bash
# =============================================================
#   Yelp Lab2 - Full Demo Setup Script
#   Run this ~25 minutes before your demo
#   Usage: bash lab2/scripts/demo_setup.sh
# =============================================================

set -e  # Exit on any error

# ── CONFIG ────────────────────────────────────────────────────
CLUSTER_NAME="yelp-lab2"
REGION="us-west-2"
NAMESPACE="yelp-lab2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/yelp-lab2"
K8S_DIR="lab2/k8s"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log()    { echo -e "${GREEN}✅ $1${NC}"; }
warn()   { echo -e "${YELLOW}⚠️  $1${NC}"; }
error()  { echo -e "${RED}❌ $1${NC}"; exit 1; }
info()   { echo -e "${BLUE}ℹ️  $1${NC}"; }
header() { echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${BLUE}  $1${NC}"; echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# ── STEP 0: Pre-flight checks ─────────────────────────────────
header "Step 0: Pre-flight Checks"

command -v aws    >/dev/null 2>&1 || error "AWS CLI not found. Install it first."
command -v kubectl >/dev/null 2>&1 || error "kubectl not found. Install it first."
command -v python3 >/dev/null 2>&1 || error "python3 not found."

aws sts get-caller-identity >/dev/null 2>&1 || error "AWS credentials not configured. Run 'aws configure'."
log "AWS credentials valid"

info "AWS Account: $ACCOUNT_ID | Region: $REGION"

# ── STEP 1: ECR Login & Build Images ─────────────────────────
header "Step 1: Login to ECR & Build Images"
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPO 2>/dev/null
log "ECR login successful"

# Check if images exist in ECR
IMAGE_COUNT=$(aws ecr describe-images --repository-name yelp-lab2 --region $REGION --query "length(imageDetails)" --output text 2>/dev/null || echo "0")

if [ "$IMAGE_COUNT" -ge 6 ]; then
    log "All 6 images found in ECR. Skipping build."
else
    warn "ECR images missing ($IMAGE_COUNT found). Building all images now..."
    info "This takes ~10-15 minutes. Please wait..."

    docker buildx build --platform linux/amd64 \
        -t ${ECR_REPO}:user-service \
        --build-arg APP_MODULE=lab2.services.user_service.app:app \
        --build-arg APP_PORT=8001 \
        -f lab2/docker/Dockerfile.service --push . && log "user-service built ✅"

    docker buildx build --platform linux/amd64 \
        -t ${ECR_REPO}:owner-service \
        --build-arg APP_MODULE=lab2.services.owner_service.app:app \
        --build-arg APP_PORT=8002 \
        -f lab2/docker/Dockerfile.service --push . && log "owner-service built ✅"

    docker buildx build --platform linux/amd64 \
        -t ${ECR_REPO}:restaurant-service \
        --build-arg APP_MODULE=lab2.services.restaurant_service.app:app \
        --build-arg APP_PORT=8003 \
        -f lab2/docker/Dockerfile.service --push . && log "restaurant-service built ✅"

    docker buildx build --platform linux/amd64 \
        -t ${ECR_REPO}:review-service \
        --build-arg APP_MODULE=lab2.services.review_service.app:app \
        --build-arg APP_PORT=8004 \
        -f lab2/docker/Dockerfile.service --push . && log "review-service built ✅"

    docker buildx build --platform linux/amd64 \
        -t ${ECR_REPO}:review-worker \
        -f lab2/docker/Dockerfile.worker --push . && log "review-worker built ✅"

    docker buildx build --platform linux/amd64 \
        -t ${ECR_REPO}:frontend \
        --build-arg REACT_APP_API_URL=http://localhost:8000 \
        -f lab2/docker/Dockerfile.frontend --push . && log "frontend built ✅"

    log "All 6 images built and pushed to ECR!"
fi

# ── STEP 2: Create EKS Cluster ───────────────────────────────
header "Step 2: Create EKS Cluster"

# Check if cluster already exists
CLUSTER_STATUS=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query "cluster.status" --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$CLUSTER_STATUS" = "ACTIVE" ]; then
    warn "Cluster '$CLUSTER_NAME' already exists and is ACTIVE. Skipping creation."
elif [ "$CLUSTER_STATUS" = "CREATING" ]; then
    warn "Cluster is already being created. Waiting for it to become ACTIVE..."
else
    info "Creating EKS cluster '$CLUSTER_NAME' in $REGION..."
    info "This takes 10-15 minutes. Please wait..."

    # Get default VPC and subnets
    VPC_ID=$(aws ec2 describe-vpcs --region $REGION --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text)
    SUBNET_IDS=$(aws ec2 describe-subnets --region $REGION --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text | tr '\t' ',')

    info "Using VPC: $VPC_ID"
    info "Using Subnets: $SUBNET_IDS"

    # Create cluster using eksctl if available, otherwise guide manually
    if command -v eksctl >/dev/null 2>&1; then
        eksctl create cluster \
            --name $CLUSTER_NAME \
            --region $REGION \
            --nodegroup-name standard-workers \
            --node-type t3.medium \
            --nodes 2 \
            --nodes-min 2 \
            --nodes-max 3 \
            --managed
    else
        warn "eksctl not found. Creating cluster via AWS CLI..."
        # Create cluster IAM role
        ROLE_ARN=$(aws iam get-role --role-name AmazonEKSAutoClusterRole --query "Role.Arn" --output text 2>/dev/null || \
                   aws iam get-role --role-name eksClusterRole --query "Role.Arn" --output text 2>/dev/null || \
                   echo "")

        if [ -z "$ROLE_ARN" ]; then
            error "No EKS cluster role found. Please create the cluster manually via AWS Console and rerun this script from Step 3."
        fi

        aws eks create-cluster \
            --name $CLUSTER_NAME \
            --region $REGION \
            --kubernetes-version 1.35 \
            --role-arn "$ROLE_ARN" \
            --resources-vpc-config subnetIds=$SUBNET_IDS,endpointPublicAccess=true \
            --output text >/dev/null

        info "Cluster creation initiated..."
    fi
fi

# Wait for cluster to become ACTIVE
info "Waiting for cluster to become ACTIVE (up to 20 minutes)..."
for i in $(seq 1 40); do
    STATUS=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query "cluster.status" --output text 2>/dev/null || echo "UNKNOWN")
    if [ "$STATUS" = "ACTIVE" ]; then
        log "Cluster is ACTIVE!"
        break
    fi
    echo -ne "  Status: $STATUS | Elapsed: $((i*30))s\r"
    sleep 30
    if [ $i -eq 40 ]; then
        error "Cluster did not become ACTIVE within 20 minutes. Check AWS Console."
    fi
done

# ── STEP 3: Configure kubectl ─────────────────────────────────
header "Step 3: Configure kubectl"
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME --alias $CLUSTER_NAME
log "kubectl configured"

# Wait for nodes to be ready
info "Waiting for worker nodes to be Ready..."
for i in $(seq 1 20); do
    READY_NODES=$(kubectl get nodes --no-headers 2>/dev/null | grep -c "Ready" || echo "0")
    if [ "$READY_NODES" -ge 1 ]; then
        log "$READY_NODES worker node(s) Ready!"
        break
    fi
    echo -ne "  Ready nodes: $READY_NODES | Elapsed: $((i*15))s\r"
    sleep 15
    if [ $i -eq 20 ]; then
        warn "No nodes ready yet. Continuing anyway..."
    fi
done

# Add IAM access entry for cli-user
info "Adding IAM access for cli-user..."
aws eks create-access-entry \
    --cluster-name $CLUSTER_NAME \
    --region $REGION \
    --principal-arn "arn:aws:iam::${ACCOUNT_ID}:user/cli-user" \
    --type STANDARD 2>/dev/null && \
aws eks associate-access-policy \
    --cluster-name $CLUSTER_NAME \
    --region $REGION \
    --principal-arn "arn:aws:iam::${ACCOUNT_ID}:user/cli-user" \
    --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
    --access-scope type=cluster 2>/dev/null || warn "Access entry may already exist"
log "IAM access configured"

# ── STEP 4: Create Namespace & ConfigMap ──────────────────────
header "Step 4: Create Namespace & ConfigMap"
kubectl create namespace $NAMESPACE 2>/dev/null || warn "Namespace already exists"
log "Namespace '$NAMESPACE' ready"

kubectl apply -f $K8S_DIR/configmap-env.yaml
log "ConfigMap applied"

# ── STEP 5: Deploy Infrastructure ─────────────────────────────
header "Step 5: Deploy Infrastructure (MongoDB + Kafka)"

# Deploy MongoDB with persistent EBS volume (gp2 StorageClass)
kubectl apply -f $K8S_DIR/deployment-mongo.yaml
log "MongoDB deployed (with persistent EBS PVC)"

kubectl apply -f $K8S_DIR/deployment-kafka.yaml
log "Kafka deployed"

# ── STEP 6: Deploy All Services ───────────────────────────────
header "Step 6: Deploy All Microservices"
kubectl apply -f $K8S_DIR/deployment-user-service.yaml
kubectl apply -f $K8S_DIR/deployment-owner-service.yaml
kubectl apply -f $K8S_DIR/deployment-restaurant-service.yaml
kubectl apply -f $K8S_DIR/deployment-review-service.yaml
kubectl apply -f $K8S_DIR/deployment-review-worker.yaml
kubectl apply -f $K8S_DIR/deployment-gateway.yaml
kubectl apply -f $K8S_DIR/deployment-frontend.yaml
log "All services deployed"

# ── STEP 7: Wait for All Pods ─────────────────────────────────
header "Step 7: Waiting for All Pods to be Running"
info "This may take 3-5 minutes while ECR images are pulled..."

for i in $(seq 1 30); do
    TOTAL=$(kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | wc -l | tr -d ' ')
    RUNNING=$(kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | grep -c "Running" || echo "0")
    echo -ne "  Pods: $RUNNING Running / $TOTAL Total | Elapsed: $((i*10))s\r"
    if [ "$RUNNING" -ge 12 ]; then
        echo ""
        log "All pods are Running!"
        break
    fi
    sleep 10
    if [ $i -eq 30 ]; then
        echo ""
        warn "Some pods may still be starting. Check with: kubectl get pods -n yelp-lab2"
    fi
done

# ── STEP 8: Wait for Gateway ALB DNS name ─────────────────────
header "Step 8: Waiting for Gateway Load Balancer DNS"
info "The AWS Load Balancer Controller will provision an NLB for the gateway..."

GATEWAY_URL=""
for i in $(seq 1 40); do
    GATEWAY_URL=$(kubectl get svc gateway -n $NAMESPACE \
        -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
    if [ -n "$GATEWAY_URL" ]; then
        log "Gateway NLB DNS: $GATEWAY_URL"
        break
    fi
    echo -ne "  Waiting for gateway LB DNS... ${i}0s elapsed\r"
    sleep 10
    if [ $i -eq 40 ]; then
        echo ""
        warn "Gateway LB DNS not assigned after 400s. Falling back to port-forward for seeding."
        GATEWAY_URL="localhost:8000"
        kubectl port-forward -n $NAMESPACE svc/gateway 8000:8000 &
        GATEWAY_PF_PID=$!
        sleep 3
    fi
done

# ── STEP 9: Rebuild Frontend with real gateway URL ────────────
header "Step 9: Rebuild Frontend Image with Gateway URL"

if [ "$GATEWAY_URL" != "localhost:8000" ]; then
    info "Rebuilding frontend with REACT_APP_API_URL=http://${GATEWAY_URL}:8000"

    docker buildx build --platform linux/amd64 \
        -t ${ECR_REPO}:frontend \
        --build-arg REACT_APP_API_URL=http://${GATEWAY_URL}:8000 \
        -f lab2/docker/Dockerfile.frontend --push .
    log "Frontend image rebuilt with real gateway URL"

    # Rolling restart so pods pick up the new image
    kubectl rollout restart deployment/frontend -n $NAMESPACE
    kubectl rollout status deployment/frontend -n $NAMESPACE --timeout=120s
    log "Frontend pods restarted with new image"
else
    warn "Skipping frontend rebuild (no public gateway URL yet)"
fi

# ── STEP 10: Wait for Frontend ALB DNS name ───────────────────
header "Step 10: Waiting for Frontend Load Balancer DNS"

FRONTEND_URL=""
for i in $(seq 1 40); do
    FRONTEND_URL=$(kubectl get svc frontend -n $NAMESPACE \
        -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
    if [ -n "$FRONTEND_URL" ]; then
        log "Frontend NLB DNS: $FRONTEND_URL"
        break
    fi
    echo -ne "  Waiting for frontend LB DNS... ${i}0s elapsed\r"
    sleep 10
    if [ $i -eq 40 ]; then
        echo ""
        warn "Frontend LB DNS not assigned. Will use port-forward as fallback."
        FRONTEND_URL=""
    fi
done

# ── STEP 11: Seed Database ─────────────────────────────────────
header "Step 11: Seeding Database with 300 Restaurants"

# Use port-forward for seeding if gateway not yet public
if [ "$GATEWAY_URL" = "localhost:8000" ]; then
    SEED_URL="http://localhost:8000"
else
    # Seed via the real gateway — wait for it to be healthy first
    info "Waiting 30s for NLB to become healthy before seeding..."
    sleep 30
    SEED_URL="http://${GATEWAY_URL}:8000"
    kill $GATEWAY_PF_PID 2>/dev/null || true
fi

GATEWAY_API_URL=$SEED_URL python3 lab2/scripts/seed_data.py
log "Database seeded!"

# Kill any lingering port-forwards from seeding
pkill -f "port-forward.*gateway" 2>/dev/null || true

# ── DONE ──────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     🎉  DEMO IS READY!                                     ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════╣${NC}"
if [ -n "$FRONTEND_URL" ]; then
echo -e "${GREEN}║  🌐 App URL:    http://${FRONTEND_URL}         ║${NC}"
else
echo -e "${YELLOW}║  🌐 App URL:    (LB pending - run kubectl get svc -n yelp-lab2)║${NC}"
fi
if [ "$GATEWAY_URL" != "localhost:8000" ]; then
echo -e "${GREEN}║  🔌 API URL:    http://${GATEWAY_URL}:8000     ║${NC}"
else
echo -e "${YELLOW}║  🔌 API URL:    http://localhost:8000 (port-forward)       ║${NC}"
fi
echo -e "${GREEN}║  👤 Test Login: test@yelp.com / Test1234!                  ║${NC}"
echo -e "${GREEN}║  🍴 Seed User:  seed@yelp.com / Seed1234!                  ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  kubectl get svc -n yelp-lab2   (to see LB URLs)          ║${NC}"
echo -e "${GREEN}║  kubectl get pods -n yelp-lab2                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
