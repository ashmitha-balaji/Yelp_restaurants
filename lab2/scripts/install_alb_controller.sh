#!/bin/bash
# =============================================================
#   Install AWS Load Balancer Controller on EKS Auto Mode
#   Run ONCE before demo_setup.sh (or add to demo_setup.sh)
#   Usage: bash lab2/scripts/install_alb_controller.sh
# =============================================================

set -e

CLUSTER_NAME="yelp-lab2"
REGION="us-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log()    { echo -e "${GREEN}✅ $1${NC}"; }
warn()   { echo -e "${YELLOW}⚠️  $1${NC}"; }
error()  { echo -e "${RED}❌ $1${NC}"; exit 1; }
info()   { echo -e "${BLUE}ℹ️  $1${NC}"; }

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Installing AWS Load Balancer Controller         ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# ── Pre-flight ─────────────────────────────────────────────
command -v helm    >/dev/null 2>&1 || error "helm not found. Install: brew install helm"
command -v kubectl >/dev/null 2>&1 || error "kubectl not found."
command -v aws     >/dev/null 2>&1 || error "aws CLI not found."
command -v eksctl  >/dev/null 2>&1 || error "eksctl not found. Install: brew tap weaveworks/tap && brew install weaveworks/tap/eksctl"

info "Account: $ACCOUNT_ID | Cluster: $CLUSTER_NAME | Region: $REGION"

# Make sure kubectl points to the right cluster
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME --alias $CLUSTER_NAME 2>/dev/null || true

# ── Step 1: Create IAM policy ──────────────────────────────
info "Step 1: Creating IAM policy for Load Balancer Controller..."

# Download the policy document
curl -sO https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.2/docs/install/iam_policy.json

# Create the policy (ignore if already exists)
aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam_policy.json \
    --no-cli-pager 2>/dev/null && log "IAM policy created" || warn "IAM policy may already exist — continuing"

rm -f iam_policy.json

# ── Step 2: Create IAM service account ────────────────────
info "Step 2: Creating IAM service account (IRSA)..."

eksctl create iamserviceaccount \
    --cluster=$CLUSTER_NAME \
    --namespace=kube-system \
    --name=aws-load-balancer-controller \
    --role-name AmazonEKSLoadBalancerControllerRole \
    --attach-policy-arn=arn:aws:iam::${ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy \
    --approve \
    --region=$REGION 2>/dev/null && log "Service account created" || warn "Service account may already exist — continuing"

# ── Step 3: Install via Helm ───────────────────────────────
info "Step 3: Installing AWS Load Balancer Controller via Helm..."

helm repo add eks https://aws.github.io/eks-charts 2>/dev/null || true
helm repo update eks

# Uninstall if exists (clean reinstall)
helm uninstall aws-load-balancer-controller -n kube-system 2>/dev/null || true
sleep 5

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
    -n kube-system \
    --set clusterName=$CLUSTER_NAME \
    --set serviceAccount.create=false \
    --set serviceAccount.name=aws-load-balancer-controller \
    --set region=$REGION \
    --set vpcId=$(aws ec2 describe-vpcs --region $REGION \
        --filters "Name=is-default,Values=true" \
        --query "Vpcs[0].VpcId" --output text)

log "Helm chart installed"

# ── Step 4: Wait for controller to be ready ───────────────
info "Step 4: Waiting for controller pods to be Ready..."
kubectl rollout status deployment/aws-load-balancer-controller -n kube-system --timeout=120s
log "AWS Load Balancer Controller is running!"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  AWS Load Balancer Controller installed! ✅      ║${NC}"
echo -e "${GREEN}║                                                  ║${NC}"
echo -e "${GREEN}║  Now run:  bash lab2/scripts/demo_setup.sh       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
