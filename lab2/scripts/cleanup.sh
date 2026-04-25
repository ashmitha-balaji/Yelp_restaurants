#!/bin/bash
# =============================================================
#   Yelp Lab2 - Cleanup Script (Run AFTER demo)
#   Deletes all AWS resources to avoid charges
#   Usage: bash lab2/scripts/cleanup.sh
# =============================================================

CLUSTER_NAME="yelp-lab2"
REGION="us-west-2"
ECR_REPO="yelp-lab2"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║   ⚠️  CLEANUP - This will DELETE everything!     ║${NC}"
echo -e "${RED}║   Run this ONLY after your demo is complete.     ║${NC}"
echo -e "${RED}╚══════════════════════════════════════════════════╝${NC}"
echo ""
read -p "Are you sure you want to delete the EKS cluster and all resources? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Step 1: Stopping port-forwards...${NC}"
pkill -f "kubectl port-forward" 2>/dev/null || true
echo -e "${GREEN}✅ Port-forwards stopped${NC}"

echo -e "${YELLOW}Step 2: Deleting Load Balancers (via kubectl)...${NC}"
kubectl patch service frontend -n yelp-lab2 -p '{"spec":{"type":"ClusterIP"}}' 2>/dev/null || true
kubectl patch service gateway -n yelp-lab2 -p '{"spec":{"type":"ClusterIP"}}' 2>/dev/null || true
sleep 10
echo -e "${GREEN}✅ Load Balancers removed${NC}"

echo -e "${YELLOW}Step 3: Deleting EKS cluster '$CLUSTER_NAME'...${NC}"
echo -e "${YELLOW}   This takes 5-10 minutes...${NC}"
aws eks delete-cluster --name $CLUSTER_NAME --region $REGION 2>/dev/null && \
    echo -e "${GREEN}✅ EKS cluster deletion initiated${NC}" || \
    echo -e "${YELLOW}⚠️  Cluster may not exist or already deleted${NC}"

echo -e "${YELLOW}Step 4: Removing kubectl context...${NC}"
kubectl config delete-context $CLUSTER_NAME 2>/dev/null || true
kubectl config delete-context arn:aws:eks:${REGION}:$(aws sts get-caller-identity --query Account --output text):cluster/${CLUSTER_NAME} 2>/dev/null || true
echo -e "${GREEN}✅ kubectl context removed${NC}"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Cleanup initiated!                             ║${NC}"
echo -e "${GREEN}║                                                  ║${NC}"
echo -e "${GREEN}║   ✅ ECR images KEPT (free tier, reusable)       ║${NC}"
echo -e "${GREEN}║   🗑️  EKS cluster being deleted (~10 min)         ║${NC}"
echo -e "${GREEN}║   🗑️  Load Balancers removed                      ║${NC}"
echo -e "${GREEN}║                                                  ║${NC}"
echo -e "${GREEN}║   Check AWS Console in 10 min to confirm.        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo "To verify deletion:"
echo "  aws eks describe-cluster --name $CLUSTER_NAME --region $REGION"
